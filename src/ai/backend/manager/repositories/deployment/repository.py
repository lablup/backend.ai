"""Main deployment repository implementation."""

import logging
import uuid
from collections import defaultdict
from collections.abc import Mapping, Sequence
from dataclasses import dataclass, field
from datetime import datetime, timedelta, timezone
from decimal import Decimal, DecimalException
from typing import Any, Optional, cast

import tomli
from pydantic import HttpUrl
from ruamel.yaml import YAML

from ai.backend.common.clients.valkey_client.valkey_live.client import ValkeyLiveClient
from ai.backend.common.clients.valkey_client.valkey_schedule.client import ValkeyScheduleClient
from ai.backend.common.clients.valkey_client.valkey_stat.client import ValkeyStatClient
from ai.backend.common.exception import BackendAIError, InvalidAPIParameters
from ai.backend.common.metrics.metric import DomainType, LayerType
from ai.backend.common.resilience.policies.metrics import MetricArgs, MetricPolicy
from ai.backend.common.resilience.policies.retry import BackoffStrategy, RetryArgs, RetryPolicy
from ai.backend.common.resilience.resilience import Resilience
from ai.backend.common.types import (
    AutoScalingMetricComparator,
    AutoScalingMetricSource,
    KernelId,
    SessionId,
)
from ai.backend.logging.utils import BraceStyleAdapter
from ai.backend.manager.data.deployment.creator import DeploymentCreator, DeploymentPolicyConfig
from ai.backend.manager.data.deployment.scale import (
    AutoScalingRule,
    AutoScalingRuleCreator,
    ModelDeploymentAutoScalingRuleCreator,
)
from ai.backend.manager.data.deployment.scale_modifier import (
    AutoScalingRuleModifier,
    ModelDeploymentAutoScalingRuleModifier,
)
from ai.backend.manager.data.deployment.types import (
    AccessTokenSearchResult,
    AutoScalingRuleSearchResult,
    DefinitionFiles,
    DeploymentInfo,
    DeploymentInfoSearchResult,
    DeploymentInfoWithAutoScalingRules,
    EndpointLifecycle,
    ModelDeploymentAutoScalingRuleData,
    ModelRevisionData,
    RevisionSearchResult,
    RouteInfo,
    RouteSearchResult,
    RouteStatus,
    ScalingGroupCleanupConfig,
)
from ai.backend.manager.data.resource.types import ScalingGroupProxyTarget
from ai.backend.manager.data.session.types import SessionStatus
from ai.backend.manager.errors.deployment import DefinitionFileNotFound
from ai.backend.manager.errors.service import EndpointNotFound
from ai.backend.manager.models.deployment_auto_scaling_policy import (
    DeploymentAutoScalingPolicyData,
    DeploymentAutoScalingPolicyRow,
)
from ai.backend.manager.models.deployment_policy import (
    DeploymentPolicyData,
    DeploymentPolicyRow,
)
from ai.backend.manager.models.deployment_revision import DeploymentRevisionRow
from ai.backend.manager.models.endpoint import EndpointRow, EndpointStatistics, EndpointTokenRow
from ai.backend.manager.models.kernel import KernelStatistics
from ai.backend.manager.models.routing import RoutingRow
from ai.backend.manager.models.storage import StorageSessionManager
from ai.backend.manager.models.utils import ExtendedAsyncSAEngine
from ai.backend.manager.models.vfolder import VFolderOwnershipType
from ai.backend.manager.repositories.base import BatchQuerier, Creator
from ai.backend.manager.repositories.base.purger import Purger, PurgerResult
from ai.backend.manager.repositories.base.updater import BatchUpdater, Updater
from ai.backend.manager.repositories.scheduler.types.session_creation import DeploymentContext

from .db_source import DeploymentDBSource
from .storage_source import DeploymentStorageSource
from .types import RouteData, RouteServiceDiscoveryInfo

log = BraceStyleAdapter(logging.getLogger(__name__))


@dataclass
class AutoScalingMetricsData:
    """Container for all metrics data needed for auto-scaling calculations."""

    kernel_statistics: dict[KernelId, Optional[Mapping[str, Any]]] = field(default_factory=dict)
    endpoint_statistics: dict[uuid.UUID, Optional[Mapping[str, Any]]] = field(default_factory=dict)
    routes_by_endpoint: Mapping[uuid.UUID, list[RouteInfo]] = field(default_factory=dict)
    kernels_by_session: dict[SessionId, list[KernelId]] = field(default_factory=dict)


deployment_repository_resilience = Resilience(
    policies=[
        MetricPolicy(
            MetricArgs(domain=DomainType.REPOSITORY, layer=LayerType.DEPLOYMENT_REPOSITORY)
        ),
        RetryPolicy(
            RetryArgs(
                max_retries=3,
                retry_delay=0.1,
                backoff_strategy=BackoffStrategy.FIXED,
                non_retryable_exceptions=(BackendAIError,),
            )
        ),
    ]
)


class DeploymentRepository:
    """Repository for deployment-related operations."""

    _db_source: DeploymentDBSource
    _storage_source: DeploymentStorageSource
    _valkey_stat: ValkeyStatClient
    _valkey_live: ValkeyLiveClient
    _valkey_schedule: ValkeyScheduleClient

    def __init__(
        self,
        db: ExtendedAsyncSAEngine,
        storage_manager: StorageSessionManager,
        valkey_stat: ValkeyStatClient,
        valkey_live: ValkeyLiveClient,
        valkey_schedule: ValkeyScheduleClient,
    ) -> None:
        self._db_source = DeploymentDBSource(db, storage_manager)
        self._storage_source = DeploymentStorageSource(storage_manager)
        self._valkey_stat = valkey_stat
        self._valkey_live = valkey_live
        self._valkey_schedule = valkey_schedule

    # Endpoint operations

    @deployment_repository_resilience.apply()
    async def create_endpoint(
        self,
        creator: Creator[EndpointRow],
        policy_config: DeploymentPolicyConfig | None = None,
    ) -> DeploymentInfo:
        """Create a new endpoint and return DeploymentInfo.

        Args:
            creator: Creator containing DeploymentCreatorSpec with resolved image_id
            policy_config: Optional deployment policy configuration

        Returns:
            DeploymentInfo for the created endpoint
        """
        return await self._db_source.create_endpoint(creator, policy_config)

    @deployment_repository_resilience.apply()
    async def create_endpoint_legacy(
        self,
        creator: DeploymentCreator,
    ) -> DeploymentInfo:
        """Create a new endpoint using legacy DeploymentCreator.

        This is for backward compatibility with legacy deployment creation flow.

        Args:
            creator: Legacy DeploymentCreator with ImageIdentifier

        Returns:
            DeploymentInfo for the created endpoint
        """
        return await self._db_source.create_endpoint_legacy(creator)

    @deployment_repository_resilience.apply()
    async def get_modified_endpoint(
        self,
        endpoint_id: uuid.UUID,
        updater: Updater[EndpointRow],
    ) -> DeploymentInfo:
        """Get modified endpoint without applying changes.

        Args:
            endpoint_id: ID of the endpoint to modify
            updater: Updater containing spec with partial updates

        Returns:
            DeploymentInfo: Modified deployment information

        Raises:
            EndpointNotFound: If the endpoint does not exist
        """
        return await self._db_source.get_modified_endpoint(endpoint_id, updater)

    @deployment_repository_resilience.apply()
    async def update_endpoint_with_spec(
        self,
        updater: Updater[EndpointRow],
    ) -> DeploymentInfo:
        """Update endpoint using an Updater.

        Args:
            updater: Updater containing spec and endpoint_id

        Returns:
            DeploymentInfo: Updated deployment information

        Raises:
            NoUpdatesToApply: If there are no updates to apply
            EndpointNotFound: If the endpoint does not exist
        """
        return await self._db_source.update_endpoint_with_spec(updater)

    @deployment_repository_resilience.apply()
    async def update_endpoint_lifecycle_bulk(
        self,
        endpoint_ids: list[uuid.UUID],
        prevoius_status: list[EndpointLifecycle],
        new_status: EndpointLifecycle,
    ) -> None:
        """Update lifecycle status for multiple endpoints."""
        await self._db_source.update_endpoint_lifecycle_bulk(
            endpoint_ids, prevoius_status, new_status
        )

    @deployment_repository_resilience.apply()
    async def get_endpoints_by_ids(
        self,
        endpoint_ids: set[uuid.UUID],
    ) -> list[DeploymentInfo]:
        """Get endpoints by their IDs."""
        return await self._db_source.get_endpoints_by_ids(endpoint_ids)

    @deployment_repository_resilience.apply()
    async def get_scaling_group_cleanup_configs(
        self, scaling_group_names: Sequence[str]
    ) -> Mapping[str, ScalingGroupCleanupConfig]:
        """
        Get route cleanup target statuses configuration for scaling groups.

        Args:
            scaling_group_names: List of scaling group names to query

        Returns:
            Mapping of scaling group name to ScalingGroupCleanupConfig
        """
        return await self._db_source.get_scaling_group_cleanup_configs(scaling_group_names)

    @deployment_repository_resilience.apply()
    async def get_endpoints_by_statuses(
        self,
        statuses: list[EndpointLifecycle],
    ) -> list[DeploymentInfo]:
        """Get endpoints by lifecycle statuses."""
        return await self._db_source.get_endpoints_by_statuses(statuses)

    @deployment_repository_resilience.apply()
    async def get_endpoint_info(
        self,
        endpoint_id: uuid.UUID,
    ) -> DeploymentInfo:
        """Get endpoint information.

        Raises:
            EndpointNotFound: If the endpoint does not exist
        """
        return await self._db_source.get_endpoint(endpoint_id)

    @deployment_repository_resilience.apply()
    async def destroy_endpoint(
        self,
        endpoint_id: uuid.UUID,
    ) -> bool:
        """Destroy an endpoint and all its routes."""
        return await self._db_source.update_endpoint_lifecycle(
            endpoint_id, EndpointLifecycle.DESTROYING
        )

    @deployment_repository_resilience.apply()
    async def delete_endpoint(
        self,
        endpoint_id: uuid.UUID,
    ) -> bool:
        """Delete an endpoint and all its routes."""
        return await self._db_source.delete_endpoint_with_routes(endpoint_id)

    @deployment_repository_resilience.apply()
    async def get_service_endpoint(
        self,
        endpoint_id: uuid.UUID,
    ) -> Optional[HttpUrl]:
        """Get service endpoint URL."""
        try:
            endpoint = await self._db_source.get_endpoint(endpoint_id)
            if not endpoint.network.url:
                return None
            return HttpUrl(endpoint.network.url)
        except EndpointNotFound:
            return None

    # Route operations

    @deployment_repository_resilience.apply()
    async def create_autoscaling_rule(
        self,
        endpoint_id: uuid.UUID,
        creator: AutoScalingRuleCreator,
    ) -> AutoScalingRule:
        """Create a new autoscaling rule for an endpoint."""
        return await self._db_source.create_autoscaling_rule(endpoint_id, creator)

    @deployment_repository_resilience.apply()
    async def list_autoscaling_rules(
        self,
        endpoint_id: uuid.UUID,
    ) -> list[AutoScalingRule]:
        """List all autoscaling rules for an endpoint."""
        return await self._db_source.list_autoscaling_rules(endpoint_id)

    @deployment_repository_resilience.apply()
    async def update_autoscaling_rule(
        self,
        rule_id: uuid.UUID,
        modifier: AutoScalingRuleModifier,
    ) -> AutoScalingRule:
        """Update an existing autoscaling rule."""
        return await self._db_source.update_autoscaling_rule(rule_id, modifier)

    @deployment_repository_resilience.apply()
    async def delete_autoscaling_rule(
        self,
        rule_id: uuid.UUID,
    ) -> bool:
        """Delete an autoscaling rule."""
        return await self._db_source.delete_autoscaling_rule(rule_id)

    # Model Deployment Auto-scaling Rule operations (new types)

    @deployment_repository_resilience.apply()
    async def create_model_deployment_autoscaling_rule(
        self,
        creator: ModelDeploymentAutoScalingRuleCreator,
    ) -> ModelDeploymentAutoScalingRuleData:
        """Create a new autoscaling rule using ModelDeployment types."""
        return await self._db_source.create_model_deployment_autoscaling_rule(creator)

    @deployment_repository_resilience.apply()
    async def update_model_deployment_autoscaling_rule(
        self,
        rule_id: uuid.UUID,
        modifier: ModelDeploymentAutoScalingRuleModifier,
    ) -> ModelDeploymentAutoScalingRuleData:
        """Update an autoscaling rule using ModelDeployment types."""
        return await self._db_source.update_model_deployment_autoscaling_rule(rule_id, modifier)

    @deployment_repository_resilience.apply()
    async def list_model_deployment_autoscaling_rules(
        self,
        endpoint_id: uuid.UUID,
    ) -> list[ModelDeploymentAutoScalingRuleData]:
        """List all autoscaling rules for an endpoint using ModelDeployment types."""
        return await self._db_source.list_model_deployment_autoscaling_rules(endpoint_id)

    @deployment_repository_resilience.apply()
    async def get_model_deployment_autoscaling_rule(
        self,
        rule_id: uuid.UUID,
    ) -> ModelDeploymentAutoScalingRuleData:
        """Get a single autoscaling rule by ID using ModelDeployment types."""
        return await self._db_source.get_model_deployment_autoscaling_rule(rule_id)

    # Data fetching operations
    @deployment_repository_resilience.apply()
    async def fetch_model_definition(
        self,
        vfolder_id: uuid.UUID,
        model_definition_path: Optional[str],
    ) -> dict[str, Any]:
        """
        Fetch model definition file from model vfolder.

        Args:
            vfolder_id: ID of the model vfolder
            definition_path: Path to the model definition file
        Returns:
            dict: Parsed model definition content
        """
        vfolder_location = await self._db_source.get_vfolder_by_id(vfolder_id)
        if vfolder_location.ownership_type == VFolderOwnershipType.GROUP:
            raise InvalidAPIParameters(
                "Cannot create model service with the project type's vfolder"
            )
        model_definition_candidates = (
            [
                model_definition_path,
            ]
            if model_definition_path
            else [
                "model-definition.yaml",
                "model-definition.yml",
            ]
        )
        model_definition_bytes = await self._storage_source.fetch_definition_file(
            vfolder_location,
            model_definition_candidates,
        )
        yaml = YAML()
        return yaml.load(model_definition_bytes)

    @deployment_repository_resilience.apply()
    async def fetch_service_definition(
        self,
        vfolder_id: uuid.UUID,
    ) -> Optional[dict[str, Any]]:
        """
        Fetch service definition file from model vfolder.

        Args:
            vfolder_id: ID of the model vfolder
        Returns:
            dict: Parsed service definition content
        """
        vfolder_location = await self._db_source.get_vfolder_by_id(vfolder_id)
        if vfolder_location.ownership_type == VFolderOwnershipType.GROUP:
            raise InvalidAPIParameters(
                "Cannot create model service with the project type's vfolder"
            )

        # Read service definition from storage
        service_definition_content: Optional[dict[str, Any]] = None
        try:
            service_definition_bytes = await self._storage_source.fetch_definition_file(
                vfolder_location,
                ["service-definition.toml"],
            )
            service_definition_content = tomli.loads(service_definition_bytes.decode("utf-8"))
        except DefinitionFileNotFound:
            # Service definition is optional
            pass

        return service_definition_content

    @deployment_repository_resilience.apply()
    async def fetch_definition_files(
        self,
        vfolder_id: uuid.UUID,
        model_definition_path: Optional[str],
    ) -> DefinitionFiles:
        """
        Fetch definition files(Both service and model definitions) from model vfolder.

        Args:
            vfolder_id: ID of the model vfolder
            definition_path: Path to the definition file
        Returns:
            DefinitionFiles: Contains service definition and model definition bytes
        """
        model_definition_content: dict[str, Any] = await self.fetch_model_definition(
            vfolder_id, model_definition_path
        )
        service_definition_content: Optional[dict[str, Any]] = await self.fetch_service_definition(
            vfolder_id
        )

        return DefinitionFiles(
            service_definition=service_definition_content,
            model_definition=model_definition_content,
        )

    @deployment_repository_resilience.apply()
    async def get_endpoints_with_autoscaling_rules(
        self,
    ) -> list[DeploymentInfoWithAutoScalingRules]:
        """Get endpoints that have autoscaling rules."""
        return await self._db_source.get_endpoints_with_autoscaling_rules()

    @deployment_repository_resilience.apply()
    async def update_autoscaling_rule_triggered(
        self,
        rule_id: uuid.UUID,
        triggered_at: datetime,
    ) -> bool:
        """Update the last triggered time for an autoscaling rule."""
        return await self._db_source.update_autoscaling_rule_triggered(rule_id, triggered_at)

    @deployment_repository_resilience.apply()
    async def batch_update_desired_replicas(
        self,
        updates: dict[uuid.UUID, int],
    ) -> None:
        """Batch update desired replicas for multiple endpoints."""
        return await self._db_source.batch_update_desired_replicas(updates)

    @deployment_repository_resilience.apply()
    async def fetch_scaling_group_proxy_targets(
        self,
        scaling_group: set[str],
    ) -> Mapping[str, Optional[ScalingGroupProxyTarget]]:
        """Fetch the proxy target URL for a scaling group endpoint."""
        return await self._db_source.fetch_scaling_group_proxy_targets(scaling_group)

    @deployment_repository_resilience.apply()
    async def fetch_auto_scaling_rules_by_endpoint_ids(
        self,
        endpoint_ids: set[uuid.UUID],
    ) -> Mapping[uuid.UUID, list[AutoScalingRule]]:
        """Fetch autoscaling rules for multiple endpoints."""
        return await self._db_source.fetch_auto_scaling_rules_by_endpoint_ids(endpoint_ids)

    @deployment_repository_resilience.apply()
    async def fetch_active_routes_by_endpoint_ids(
        self,
        endpoint_ids: set[uuid.UUID],
    ) -> Mapping[uuid.UUID, list[RouteInfo]]:
        """Fetch routes for multiple endpoints."""
        return await self._db_source.fetch_active_routes_by_endpoint_ids(endpoint_ids)

    @deployment_repository_resilience.apply()
    async def scale_routes(
        self,
        scale_out_creators: Sequence[Creator[RoutingRow]],
        scale_in_updater: BatchUpdater[RoutingRow] | None,
    ) -> None:
        await self._db_source.scale_routes(scale_out_creators, scale_in_updater)

    # Route operations

    @deployment_repository_resilience.apply()
    async def get_routes_by_statuses(
        self,
        statuses: list[RouteStatus],
    ) -> list[RouteData]:
        """Get routes by their statuses.

        Args:
            statuses: List of route statuses to filter by

        Returns:
            List of RouteData objects matching the statuses
        """
        return await self._db_source.get_routes_by_statuses(statuses)

    @deployment_repository_resilience.apply()
    async def update_route_status_bulk(
        self,
        route_ids: set[uuid.UUID],
        previous_statuses: list[RouteStatus],
        new_status: RouteStatus,
    ) -> None:
        """Update status for multiple routes.

        Args:
            route_ids: IDs of routes to update
            previous_statuses: Current statuses to validate against
            new_status: New status to set
        """
        await self._db_source.update_route_status_bulk(route_ids, previous_statuses, new_status)

    @deployment_repository_resilience.apply()
    async def mark_terminating_route_status_bulk(
        self,
        route_ids: set[uuid.UUID],
    ) -> None:
        """Update status for multiple routes.

        Args:
            route_ids: IDs of routes to update
            previous_statuses: Current statuses to validate against
            new_status: New status to set
        """
        await self._db_source.mark_terminating_route_status_bulk(route_ids)

    @deployment_repository_resilience.apply()
    async def update_desired_replicas_bulk(
        self,
        replica_updates: Mapping[uuid.UUID, int],
    ) -> None:
        """Update desired replicas for multiple endpoints.

        Args:
            replica_updates: Mapping of endpoint IDs to new desired replica counts
        """
        await self._db_source.update_desired_replicas_bulk(replica_updates)

    @deployment_repository_resilience.apply()
    async def update_endpoint_urls_bulk(
        self,
        url_updates: Mapping[uuid.UUID, str],
    ) -> None:
        """Update endpoint URLs for multiple endpoints.

        Args:
            url_updates: Mapping of endpoint IDs to their registered URLs
        """
        await self._db_source.update_endpoint_urls_bulk(url_updates)

    @deployment_repository_resilience.apply()
    async def update_route_sessions(
        self,
        route_session_ids: Mapping[uuid.UUID, SessionId],
    ) -> None:
        """Update session IDs for multiple routes and initialize their health status.

        Args:
            route_session_ids: Mapping of route IDs to new session IDs
        """
        # Update sessions in database
        await self._db_source.update_route_sessions(route_session_ids)
        route_id_strings = [str(route_id) for route_id in route_session_ids.keys()]
        await self._valkey_schedule.initialize_routes_health_status_batch(route_id_strings)

    @deployment_repository_resilience.apply()
    async def delete_routes_by_route_ids(
        self,
        route_ids: set[uuid.UUID],
    ) -> None:
        """Delete routes by their IDs.

        Args:
            route_ids: List of route IDs to delete
        """
        await self._db_source.delete_routes_by_route_ids(route_ids)

    @deployment_repository_resilience.apply()
    async def fetch_deployment_context(
        self,
        deployment_info: DeploymentInfo,
    ) -> DeploymentContext:
        """Fetch all context data needed for session creation from deployment info.

        Args:
            deployment_info: Deployment information

        Returns:
            DeploymentContext: Context data needed for session creation
        """
        return await self._db_source.fetch_deployment_context(deployment_info)

    # Auto-scaling operations

    @deployment_repository_resilience.apply()
    async def fetch_metrics_for_autoscaling(
        self,
        deployments: Sequence[DeploymentInfo],
        auto_scaling_rules: Mapping[uuid.UUID, Sequence[AutoScalingRule]],
    ) -> AutoScalingMetricsData:
        """Fetch all metrics needed for auto-scaling calculations.

        Args:
            deployments: List of deployments to fetch metrics for
            auto_scaling_rules: Auto-scaling rules by endpoint ID

        Returns:
            AutoScalingMetricsData containing all metrics needed for calculations
        """
        # Collect endpoint IDs
        endpoint_ids = {deployment.id for deployment in deployments}

        # Fetch routes for all endpoints
        routes_by_endpoint = await self._db_source.fetch_active_routes_by_endpoint_ids(endpoint_ids)

        # Determine which metrics we need to fetch based on rules
        metric_requested_sessions: list[SessionId] = []
        metric_requested_kernels: list[KernelId] = []
        metric_requested_endpoints: list[uuid.UUID] = []
        kernels_by_session_id: dict[SessionId, list[KernelId]] = defaultdict(list)

        for deployment in deployments:
            rules = auto_scaling_rules.get(deployment.id, [])
            for rule in rules:
                if rule.condition.metric_source == AutoScalingMetricSource.KERNEL:
                    # Need to fetch kernel metrics for this endpoint's sessions
                    for route in routes_by_endpoint.get(deployment.id, []):
                        if route.session_id:
                            metric_requested_sessions.append(route.session_id)
                elif rule.condition.metric_source == AutoScalingMetricSource.INFERENCE_FRAMEWORK:
                    # Need to fetch endpoint metrics
                    metric_requested_endpoints.append(deployment.id)

        # Fetch kernel data if needed
        if metric_requested_sessions:
            # Fetch kernels for sessions
            kernel_rows = await self._db_source.fetch_kernels_by_session_ids(
                list(set(metric_requested_sessions))
            )
            for kernel_id, session_id in kernel_rows:
                kernels_by_session_id[session_id].append(kernel_id)
                metric_requested_kernels.append(kernel_id)

        # Batch fetch metrics from Valkey
        kernel_statistics_by_id: dict[KernelId, Optional[Mapping[str, Any]]] = {}
        endpoint_statistics_by_id: dict[uuid.UUID, Optional[Mapping[str, Any]]] = {}

        if metric_requested_kernels:
            kernel_live_stats = await KernelStatistics.batch_load_by_kernel_impl(
                self._valkey_stat,
                cast(list[SessionId], metric_requested_kernels),
            )
            kernel_statistics_by_id = {
                kernel_id: metric
                for kernel_id, metric in zip(metric_requested_kernels, kernel_live_stats)
            }

        if metric_requested_endpoints:
            endpoint_live_stats = await EndpointStatistics.batch_load_by_endpoint_impl(
                self._valkey_stat,
                cast(list[uuid.UUID], metric_requested_endpoints),
            )
            endpoint_statistics_by_id = {
                endpoint_id: metric
                for endpoint_id, metric in zip(metric_requested_endpoints, endpoint_live_stats)
            }

        return AutoScalingMetricsData(
            kernel_statistics=kernel_statistics_by_id,
            endpoint_statistics=endpoint_statistics_by_id,
            routes_by_endpoint=routes_by_endpoint,
            kernels_by_session=kernels_by_session_id,
        )

    @deployment_repository_resilience.apply()
    async def calculate_desired_replicas_for_deployment(
        self,
        deployment: DeploymentInfo,
        auto_scaling_rules: Sequence[AutoScalingRule],
        metrics_data: AutoScalingMetricsData,
    ) -> Optional[int]:
        """Calculate desired replicas for a deployment based on auto-scaling rules.

        Args:
            deployment: Deployment to calculate for
            auto_scaling_rules: Auto-scaling rules to evaluate
            metrics_data: All metrics data needed for calculations

        Returns:
            Desired replica count if change is needed, None otherwise
        """
        if not auto_scaling_rules:
            return None

        current_datetime = datetime.now(timezone.utc)
        current_replica_count = deployment.replica_spec.target_replica_count
        routes = metrics_data.routes_by_endpoint.get(deployment.id, [])

        for rule in auto_scaling_rules:
            # Calculate current metric value based on source
            current_value: Optional[Decimal] = None
            should_trigger = False

            if rule.condition.metric_source == AutoScalingMetricSource.KERNEL:
                # Aggregate kernel metrics
                metric_aggregated_value = Decimal("0")
                metric_found_kernel_count = 0

                for route in routes:
                    if route.session_id:
                        for kernel_id in metrics_data.kernels_by_session.get(route.session_id, []):
                            kernel_stat = metrics_data.kernel_statistics.get(kernel_id)
                            if not kernel_stat:
                                continue
                            if rule.condition.metric_name not in kernel_stat:
                                continue
                            metric_found_kernel_count += 1
                            metric_value = cast(
                                dict[str, Any], kernel_stat[rule.condition.metric_name]
                            )
                            metric_aggregated_value += Decimal(str(metric_value.get("pct", 0)))

                if metric_found_kernel_count == 0:
                    log.warning(
                        "AUTOSCALE(e:{}, rule:{}): skipping - metric {} not found",
                        deployment.id,
                        rule.id,
                        rule.condition.metric_name,
                    )
                    continue

                current_value = metric_aggregated_value / Decimal(metric_found_kernel_count)

            elif rule.condition.metric_source == AutoScalingMetricSource.INFERENCE_FRAMEWORK:
                # Use endpoint metrics
                endpoint_stat = metrics_data.endpoint_statistics.get(deployment.id)
                if not endpoint_stat:
                    log.warning(
                        "AUTOSCALE(e:{}, rule:{}): skipping - no endpoint statistics",
                        deployment.id,
                        rule.id,
                    )
                    continue
                if rule.condition.metric_name not in endpoint_stat:
                    log.warning(
                        "AUTOSCALE(e:{}, rule:{}): skipping - metric {} not found",
                        deployment.id,
                        rule.id,
                        rule.condition.metric_name,
                    )
                    continue

                metric_value = cast(dict[str, Any], endpoint_stat[rule.condition.metric_name])
                route_count = len(routes) if routes else 1
                metric_type = metric_value.get("__type")
                match metric_type:
                    case "HISTOGRAM":
                        log.exception("Unable to set auto-scaling rule on histogram metrics. Skip")
                        continue
                    case "GAUGE" | "COUNTER" | _:
                        current_metric_value = metric_value.get("current", 0)
                        try:
                            current_value = Decimal(str(current_metric_value)) / Decimal(
                                route_count
                            )
                        except DecimalException:
                            log.exception(
                                "Unable parse metric value '{}' to decimal. Skip",
                                current_metric_value,
                            )
                            continue

            else:
                log.warning(
                    "AUTOSCALE(e:{}, rule:{}): unknown metric source {}",
                    deployment.id,
                    rule.id,
                    rule.condition.metric_source,
                )
                continue

            # Evaluate threshold comparison
            if current_value is not None:
                threshold = Decimal(rule.condition.threshold)

                if rule.condition.comparator == AutoScalingMetricComparator.LESS_THAN:
                    should_trigger = current_value < threshold
                elif rule.condition.comparator == AutoScalingMetricComparator.LESS_THAN_OR_EQUAL:
                    should_trigger = current_value <= threshold
                elif rule.condition.comparator == AutoScalingMetricComparator.GREATER_THAN:
                    should_trigger = current_value > threshold
                elif rule.condition.comparator == AutoScalingMetricComparator.GREATER_THAN_OR_EQUAL:
                    should_trigger = current_value >= threshold

                log.debug(
                    "AUTOSCALE(e:{}, rule:{}): {} {} {}: {}",
                    deployment.id,
                    rule.id,
                    current_value,
                    rule.condition.comparator.value,
                    threshold,
                    should_trigger,
                )

            if should_trigger:
                # Calculate new replica count
                new_replica_count = max(0, current_replica_count + rule.action.step_size)

                # Check min/max limits
                if (
                    rule.action.min_replicas is not None
                    and new_replica_count < rule.action.min_replicas
                ):
                    log.info(
                        "AUTOSCALE(e:{}, rule:{}): new count {} below min {}",
                        deployment.id,
                        rule.id,
                        new_replica_count,
                        rule.action.min_replicas,
                    )
                    continue

                if (
                    rule.action.max_replicas is not None
                    and new_replica_count > rule.action.max_replicas
                ):
                    log.info(
                        "AUTOSCALE(e:{}, rule:{}): new count {} above max {}",
                        deployment.id,
                        rule.id,
                        new_replica_count,
                        rule.action.max_replicas,
                    )
                    continue

                # Check cooldown period
                if rule.last_triggered_at is not None:
                    cooldown_end = rule.last_triggered_at + timedelta(
                        seconds=rule.action.cooldown_seconds
                    )
                    if current_datetime < cooldown_end:
                        log.info(
                            "AUTOSCALE(e:{}, rule:{}): in cooldown until {}",
                            deployment.id,
                            rule.id,
                            cooldown_end,
                        )
                        continue

                log.info(
                    "AUTOSCALE(e:{}, rule:{}): triggering scale from {} to {}",
                    deployment.id,
                    rule.id,
                    current_replica_count,
                    new_replica_count,
                )

                # Update last triggered time
                await self._db_source.update_autoscaling_rule_triggered(rule.id, current_datetime)

                return new_replica_count

        return None

    @deployment_repository_resilience.apply()
    async def fetch_session_statuses_by_route_ids(
        self,
        route_ids: set[uuid.UUID],
    ) -> Mapping[uuid.UUID, Optional[SessionStatus]]:
        """Fetch session IDs for multiple routes."""
        return await self._db_source.fetch_session_statuses_by_route_ids(route_ids)

    @deployment_repository_resilience.apply()
    async def update_endpoint_route_info(
        self,
        endpoint_id: uuid.UUID,
    ) -> None:
        # Generate route connection info
        connection_info = await self._db_source.generate_route_connection_info(endpoint_id)

        # Get health check config
        health_check_config = await self._db_source.get_endpoint_health_check_config(endpoint_id)

        # Update Redis with route info
        await self._valkey_live.update_appproxy_redis_info(
            endpoint_id,
            connection_info,
            health_check_config,
        )

    @deployment_repository_resilience.apply()
    async def get_endpoint_id_by_session(
        self,
        session_id: uuid.UUID,
    ) -> Optional[uuid.UUID]:
        """
        Get endpoint ID associated with a session.

        Args:
            session_id: ID of the session

        Returns:
            Endpoint ID if found, None otherwise
        """
        return await self._db_source.get_endpoint_id_by_session(session_id)

    @deployment_repository_resilience.apply()
    async def fetch_route_service_discovery_info(
        self,
        route_ids: set[uuid.UUID],
    ) -> list[RouteServiceDiscoveryInfo]:
        """Fetch service discovery information for routes.

        Args:
            route_ids: Set of route IDs to fetch information for

        Returns:
            List of RouteServiceDiscoveryInfo containing kernel host/port and endpoint details
        """
        return await self._db_source.fetch_route_service_discovery_info(route_ids)

    @deployment_repository_resilience.apply()
    async def get_default_architecture_from_scaling_group(
        self, scaling_group_name: str
    ) -> Optional[str]:
        """
        Get the default (most common) architecture from active agents in a scaling group.
        Returns None if no active agents exist.
        """
        return await self._db_source.get_default_architecture_from_scaling_group(scaling_group_name)

    # ========== Deployment Revision Operations ==========

    @deployment_repository_resilience.apply()
    async def create_revision(
        self,
        creator: Creator[DeploymentRevisionRow],
    ) -> ModelRevisionData:
        """Create a new deployment revision."""
        return await self._db_source.create_revision(creator)

    @deployment_repository_resilience.apply()
    async def get_revision(
        self,
        revision_id: uuid.UUID,
    ) -> ModelRevisionData:
        """Get a deployment revision by ID.

        Raises:
            DeploymentRevisionNotFound: If the revision does not exist.
        """
        return await self._db_source.get_revision(revision_id)

    @deployment_repository_resilience.apply()
    async def get_revision_by_route_id(
        self,
        route_id: uuid.UUID,
    ) -> ModelRevisionData:
        """Get a deployment revision by route (replica) ID.

        Args:
            route_id: ID of the route (replica)

        Raises:
            RouteNotFound: If the route does not exist.
            DeploymentRevisionNotFound: If the route has no revision linked.
        """
        return await self._db_source.get_revision_by_route_id(route_id)

    @deployment_repository_resilience.apply()
    async def get_current_revision(
        self,
        endpoint_id: uuid.UUID,
    ) -> ModelRevisionData:
        """Get the current revision of a deployment.

        Args:
            endpoint_id: ID of the deployment endpoint

        Raises:
            EndpointNotFound: If the endpoint does not exist.
            DeploymentRevisionNotFound: If the endpoint has no current revision.
        """
        return await self._db_source.get_current_revision(endpoint_id)

    @deployment_repository_resilience.apply()
    async def search_revisions(
        self,
        querier: BatchQuerier,
    ) -> RevisionSearchResult:
        """Search deployment revisions with pagination and filtering."""
        return await self._db_source.search_revisions(querier)

    @deployment_repository_resilience.apply()
    async def get_latest_revision_number(
        self,
        endpoint_id: uuid.UUID,
    ) -> Optional[int]:
        """Get the latest revision number for an endpoint.

        Returns None if no revisions exist for the endpoint.
        """
        return await self._db_source.get_latest_revision_number(endpoint_id)

    @deployment_repository_resilience.apply()
    async def update_endpoint(
        self,
        updater: Updater[EndpointRow],
    ) -> DeploymentInfo:
        """Update an endpoint using the provided updater spec.

        Returns:
            DeploymentInfo: The updated endpoint information.

        Raises:
            EndpointNotFound: If the endpoint does not exist.
        """
        return await self._db_source.update_endpoint(updater)

    @deployment_repository_resilience.apply()
    async def update_current_revision(
        self,
        endpoint_id: uuid.UUID,
        revision_id: uuid.UUID,
    ) -> uuid.UUID | None:
        """Update the current revision of a deployment.

        Returns:
            The previous revision ID, or None if there was no previous revision.
        """
        return await self._db_source.update_current_revision(endpoint_id, revision_id)

    # ========== Deployment Auto-Scaling Policy Operations ==========

    @deployment_repository_resilience.apply()
    async def create_auto_scaling_policy(
        self,
        creator: Creator[DeploymentAutoScalingPolicyRow],
    ) -> DeploymentAutoScalingPolicyData:
        """Create a new auto-scaling policy for an endpoint."""
        return await self._db_source.create_auto_scaling_policy(creator)

    @deployment_repository_resilience.apply()
    async def get_auto_scaling_policy(
        self,
        endpoint_id: uuid.UUID,
    ) -> DeploymentAutoScalingPolicyData:
        """Get the auto-scaling policy for an endpoint.

        Raises:
            AutoScalingPolicyNotFound: If no policy exists for the endpoint.
        """
        return await self._db_source.get_auto_scaling_policy(endpoint_id)

    @deployment_repository_resilience.apply()
    async def update_auto_scaling_policy(
        self,
        updater: Updater[DeploymentAutoScalingPolicyRow],
    ) -> DeploymentAutoScalingPolicyData:
        """Update an auto-scaling policy.

        Raises:
            AutoScalingPolicyNotFound: If the policy does not exist.
        """
        return await self._db_source.update_auto_scaling_policy(updater)

    @deployment_repository_resilience.apply()
    async def delete_auto_scaling_policy(
        self,
        purger: Purger[DeploymentAutoScalingPolicyRow],
    ) -> PurgerResult[DeploymentAutoScalingPolicyRow] | None:
        """Delete an auto-scaling policy by primary key.

        Returns:
            PurgerResult containing the deleted row, or None if no policy existed.
        """
        return await self._db_source.delete_auto_scaling_policy(purger)

    @deployment_repository_resilience.apply()
    async def create_deployment_policy(
        self,
        creator: Creator[DeploymentPolicyRow],
    ) -> DeploymentPolicyData:
        """Create a new deployment policy for an endpoint."""
        return await self._db_source.create_deployment_policy(creator)

    @deployment_repository_resilience.apply()
    async def get_deployment_policy(
        self,
        endpoint_id: uuid.UUID,
    ) -> DeploymentPolicyData:
        """Get the deployment policy for an endpoint.

        Raises:
            DeploymentPolicyNotFound: If no policy exists for the endpoint.
        """
        return await self._db_source.get_deployment_policy(endpoint_id)

    @deployment_repository_resilience.apply()
    async def update_deployment_policy(
        self,
        updater: Updater[DeploymentPolicyRow],
    ) -> DeploymentPolicyData:
        """Update a deployment policy.

        Raises:
            DeploymentPolicyNotFound: If the policy does not exist.
        """
        return await self._db_source.update_deployment_policy(updater)

    @deployment_repository_resilience.apply()
    async def delete_deployment_policy(
        self,
        purger: Purger[DeploymentPolicyRow],
    ) -> PurgerResult[DeploymentPolicyRow] | None:
        """Delete a deployment policy by primary key.

        Returns:
            PurgerResult containing the deleted row, or None if no policy existed.
        """
        return await self._db_source.delete_deployment_policy(purger)

    # ===================
    # Route operations
    # ===================

    @deployment_repository_resilience.apply()
    async def create_route(
        self,
        creator: Creator[RoutingRow],
    ) -> uuid.UUID:
        """Create a new route using the provided creator.

        The Creator contains a RouteCreatorSpec that defines the route properties.

        Returns:
            UUID of the newly created route.
        """
        return await self._db_source.create_route(creator)

    @deployment_repository_resilience.apply()
    async def update_route(
        self,
        updater: Updater[RoutingRow],
    ) -> bool:
        """Update a route using the provided updater.

        The Updater contains a RouteUpdaterSpec or RouteStatusUpdaterSpec
        that defines which fields to update.

        Returns:
            True if the route was updated, False if not found.
        """
        return await self._db_source.update_route(updater)

    @deployment_repository_resilience.apply()
    async def search_routes(
        self,
        querier: BatchQuerier,
    ) -> RouteSearchResult:
        """Search routes with pagination and filtering.

        Args:
            querier: BatchQuerier containing conditions, orders, and pagination

        Returns:
            RouteSearchResult with items, total_count, and pagination info
        """
        return await self._db_source.search_routes(querier)

    @deployment_repository_resilience.apply()
    async def get_route(
        self,
        route_id: uuid.UUID,
    ) -> Optional[RouteInfo]:
        """Get a route by ID.

        Args:
            route_id: ID of the route (replica)

        Returns:
            RouteInfo if found, None otherwise
        """
        return await self._db_source.get_route(route_id)

    @deployment_repository_resilience.apply()
    async def search_endpoints(
        self,
        querier: BatchQuerier,
    ) -> DeploymentInfoSearchResult:
        """Search endpoints with pagination and filtering.

        Args:
            querier: BatchQuerier containing conditions, orders, and pagination

        Returns:
            DeploymentInfoSearchResult with items, total_count, and pagination info
        """
        return await self._db_source.search_endpoints(querier)

    # ========== Access Token Operations ==========

    @deployment_repository_resilience.apply()
    async def create_access_token(
        self,
        creator: Creator[EndpointTokenRow],
    ) -> EndpointTokenRow:
        """Create a new access token for a model deployment.

        Args:
            creator: Creator containing the EndpointTokenCreatorSpec.

        Returns:
            Created EndpointTokenRow.
        """
        return await self._db_source.create_access_token(creator)

    # ========== Additional Search Operations ==========

    @deployment_repository_resilience.apply()
    async def search_auto_scaling_rules(
        self,
        querier: BatchQuerier,
    ) -> AutoScalingRuleSearchResult:
        """Search auto-scaling rules with pagination and filtering.

        Args:
            querier: BatchQuerier containing conditions, orders, and pagination.

        Returns:
            AutoScalingRuleSearchResult with items, total_count, and pagination info.
        """
        return await self._db_source.search_auto_scaling_rules(querier)

    @deployment_repository_resilience.apply()
    async def search_access_tokens(
        self,
        querier: BatchQuerier,
    ) -> AccessTokenSearchResult:
        """Search access tokens with pagination and filtering.

        Args:
            querier: BatchQuerier containing conditions, orders, and pagination.

        Returns:
            AccessTokenSearchResult with items, total_count, and pagination info.
        """
        return await self._db_source.search_access_tokens(querier)
