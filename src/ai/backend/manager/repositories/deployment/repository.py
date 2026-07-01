"""Main deployment repository implementation."""

import logging
import uuid
from collections import defaultdict
from collections.abc import Iterable, Mapping, Sequence
from dataclasses import dataclass, field
from datetime import UTC, datetime, timedelta
from decimal import Decimal, DecimalException
from typing import Any, cast

from pydantic import HttpUrl

from ai.backend.common.clients.valkey_client.valkey_live.client import ValkeyLiveClient
from ai.backend.common.clients.valkey_client.valkey_schedule.client import ValkeyScheduleClient
from ai.backend.common.clients.valkey_client.valkey_stat.client import ValkeyStatClient
from ai.backend.common.config import ModelHealthCheck
from ai.backend.common.data.endpoint.types import EndpointLifecycle
from ai.backend.common.exception import BackendAIError, InvalidAPIParameters
from ai.backend.common.identifier.deployment import DeploymentID
from ai.backend.common.identifier.deployment_preset import DeploymentPresetID
from ai.backend.common.identifier.deployment_revision import DeploymentRevisionID
from ai.backend.common.identifier.image import ImageID
from ai.backend.common.identifier.replica import ReplicaID
from ai.backend.common.identifier.resource_group import ResourceGroupName
from ai.backend.common.identifier.runtime_variant import RuntimeVariantID
from ai.backend.common.identifier.vfolder import VFolderUUID
from ai.backend.common.metrics.metric import DomainType, LayerType
from ai.backend.common.resilience.policies.metrics import MetricArgs, MetricPolicy
from ai.backend.common.resilience.policies.retry import BackoffStrategy, RetryArgs, RetryPolicy
from ai.backend.common.resilience.resilience import Resilience
from ai.backend.common.types import (
    AutoScalingMetricSource,
    KernelId,
    MountPermission,
    SessionId,
    SlotName,
    VFolderUsageMode,
)
from ai.backend.logging.utils import BraceStyleAdapter
from ai.backend.manager.clients.valkey_client.statistics import (
    EndpointStatistics,
    KernelStatistics,
)
from ai.backend.manager.data.deployment.creator import DeploymentPolicyConfig
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
    DeploymentConfig,
    DeploymentHandlerCategory,
    DeploymentInfo,
    DeploymentInfoSearchResult,
    DeploymentInfoWithAutoScalingRules,
    DeploymentOptions,
    DeploymentPolicyData,
    DeploymentPolicySearchResult,
    DeploymentPolicyUpsertResult,
    DeploymentRevisionReadBundle,
    DeploymentSummarySearchResult,
    DeploymentWithHistory,
    FetchedModelDefinition,
    LegacyRevisionCreateReadBundle,
    ModelDeploymentAccessTokenData,
    ModelDeploymentAutoScalingRuleData,
    ModelRevisionData,
    RevisionSearchResult,
    RouteHandlerCategory,
    RouteInfo,
    RouteSearchResult,
    RouteStatus,
    ScalingGroupCleanupConfig,
)
from ai.backend.manager.data.image.types import ImageIdentifier
from ai.backend.manager.data.model_serving.types import AppProxyRouteEntry
from ai.backend.manager.data.resource.types import ScalingGroupProxyTarget
from ai.backend.manager.data.session.creation import DeploymentContext
from ai.backend.manager.data.session.types import SessionStatus
from ai.backend.manager.errors.service import EndpointNotFound
from ai.backend.manager.models.deployment_policy import DeploymentPolicyRow
from ai.backend.manager.models.deployment_revision import DeploymentRevisionRow
from ai.backend.manager.models.endpoint import EndpointRow, EndpointTokenRow
from ai.backend.manager.models.routing import RoutingRow
from ai.backend.manager.models.scheduling_history import (
    RouteHistoryRow,
)
from ai.backend.manager.models.storage import StorageSessionManager
from ai.backend.manager.models.utils import ExtendedAsyncSAEngine
from ai.backend.manager.models.vfolder import VFolderOwnershipType
from ai.backend.manager.repositories.base import BatchQuerier
from ai.backend.manager.repositories.base.creator import BulkCreator
from ai.backend.manager.repositories.base.purger import Purger, PurgerResult
from ai.backend.manager.repositories.base.rbac.entity_creator import RBACEntityCreator
from ai.backend.manager.repositories.base.updater import (
    BatchUpdater,
    Updater,
)
from ai.backend.manager.repositories.base.upserter import Upserter
from ai.backend.manager.repositories.scheduling_history.creators import DeploymentHistoryCreatorSpec

from .db_source import DeploymentDBSource
from .storage_source import DeploymentStorageSource
from .types import (
    ProjectDeploymentSearchScope,
    RouteData,
    RouteServiceDiscoveryInfo,
    RouteSessionInfo,
    RouteSessionKernelInfo,
)

log = BraceStyleAdapter(logging.getLogger(__name__))

_DEPLOYMENT_CONFIG_FILENAME = "deployment-config.yaml"
_LEGACY_SERVICE_DEFINITION_FILENAME = "service-definition.toml"


@dataclass
class AutoScalingMetricsData:
    """Container for all metrics data needed for auto-scaling calculations."""

    kernel_statistics: dict[KernelId, Mapping[str, Any] | None] = field(default_factory=dict)
    deployment_statistics: dict[DeploymentID, Mapping[str, Any] | None] = field(
        default_factory=dict
    )
    routes_by_deployment: Mapping[DeploymentID, list[RouteInfo]] = field(default_factory=dict)
    kernels_by_session: dict[SessionId, list[KernelId]] = field(default_factory=dict)
    prometheus_metrics: dict[uuid.UUID, Decimal] = field(default_factory=dict)


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
        creator: RBACEntityCreator[EndpointRow],
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
    async def get_image_id(self, image: ImageIdentifier) -> ImageID:
        """Get image ID from ImageIdentifier."""
        return await self._db_source.get_image_id(image)

    @deployment_repository_resilience.apply()
    async def get_default_architecture_from_scaling_group(
        self, scaling_group_name: str
    ) -> str | None:
        """Most common architecture among live agents in a scaling group.

        Used as the lowest-priority fallback when a legacy request supplies
        only the image canonical without an explicit architecture. Returns
        ``None`` when no live agents are attached to the scaling group.
        """
        return await self._db_source.get_default_architecture_from_scaling_group(scaling_group_name)

    @deployment_repository_resilience.apply()
    async def get_modified_endpoint(
        self,
        endpoint_id: DeploymentID,
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
        endpoint_ids: list[DeploymentID],
        prevoius_status: list[EndpointLifecycle],
        new_status: EndpointLifecycle,
    ) -> None:
        """Update lifecycle status for multiple endpoints."""
        await self._db_source.update_endpoint_lifecycle_bulk(
            endpoint_ids, prevoius_status, new_status
        )

    @deployment_repository_resilience.apply()
    async def update_endpoint_lifecycle_bulk_with_history(
        self,
        batch_updaters: Sequence[BatchUpdater[EndpointRow]],
        *,
        new_history_specs: Sequence[DeploymentHistoryCreatorSpec],
        merge_history_ids: Sequence[uuid.UUID],
    ) -> int:
        """Update lifecycle status and record history in same transaction.

        The coordinator decides merge vs create; this is a pure writer.

        Args:
            batch_updaters: BatchUpdaters for endpoint-status updates.
            new_history_specs: Specs to INSERT.
            merge_history_ids: Existing history-row ids whose
                ``attempts`` should be incremented.
        """
        return await self._db_source.update_endpoint_lifecycle_bulk_with_history(
            batch_updaters,
            new_history_specs=new_history_specs,
            merge_history_ids=merge_history_ids,
        )

    @deployment_repository_resilience.apply()
    async def get_deployments_by_ids(
        self,
        deployment_ids: set[DeploymentID],
    ) -> list[DeploymentInfo]:
        """Get deployments by their IDs."""
        return await self._db_source.get_deployments_by_ids(deployment_ids)

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
    async def get_resource_group_default_deployment_options(
        self, resource_group_name: ResourceGroupName
    ) -> DeploymentOptions:
        """Return the resource group's ``default_deployment_options``.

        Controllers snapshot this onto the new deployment at create
        time so later changes to the resource group do not propagate
        to existing deployments.
        """
        return await self._db_source.get_resource_group_default_deployment_options(
            resource_group_name
        )

    @deployment_repository_resilience.apply()
    async def search_deployments_with_last_history(
        self,
        *,
        querier: BatchQuerier,
        category: DeploymentHandlerCategory,
    ) -> list[DeploymentWithHistory]:
        """Search deployments via ``querier`` and attach the last history
        row scoped to ``category`` (or ``None``) to each result.

        The coordinator compares ``last_history.phase`` with the current
        handler name at failure-classification time to decide whether to
        carry retry counts forward.
        """
        return await self._db_source.search_deployments_with_last_history(
            querier=querier,
            category=category,
        )

    @deployment_repository_resilience.apply()
    async def get_endpoint_info(
        self,
        endpoint_id: DeploymentID,
    ) -> DeploymentInfo:
        """Get endpoint information (modern, light: revision *ids* only).

        Raises:
            EndpointNotFound: If the endpoint does not exist
        """
        return await self._db_source.get_endpoint(endpoint_id)

    @deployment_repository_resilience.apply()
    async def get_legacy_endpoint_info(
        self,
        endpoint_id: DeploymentID,
    ) -> DeploymentInfo:
        """Get endpoint information (legacy, full: includes the current/deploying
        revision data). DO NOT USE in new code — for the REST v1 surface only.

        Raises:
            EndpointNotFound: If the endpoint does not exist
        """
        return await self._db_source.get_legacy_endpoint(endpoint_id)

    @deployment_repository_resilience.apply()
    async def destroy_endpoint(
        self,
        endpoint_id: DeploymentID,
    ) -> bool:
        """Destroy an endpoint and all its routes."""
        return await self._db_source.update_endpoint_lifecycle(
            endpoint_id, EndpointLifecycle.DESTROYING
        )

    @deployment_repository_resilience.apply()
    async def replace_deployment_options(
        self,
        deployment_id: DeploymentID,
        options: DeploymentOptions,
    ) -> DeploymentOptions:
        """Fully replace a deployment's ``options`` surface.

        Returns the persisted :class:`DeploymentOptions` value in a
        single ``UPDATE ... RETURNING`` round-trip. Callers that need
        the full deployment node should re-read separately.

        Raises:
            EndpointNotFound: If the deployment does not exist.
        """
        return await self._db_source.replace_deployment_options(deployment_id, options)

    @deployment_repository_resilience.apply()
    async def delete_endpoint(
        self,
        endpoint_id: DeploymentID,
    ) -> bool:
        """Delete an endpoint and all its routes."""
        return await self._db_source.delete_endpoint_with_routes(endpoint_id)

    @deployment_repository_resilience.apply()
    async def get_service_endpoint(
        self,
        endpoint_id: DeploymentID,
    ) -> HttpUrl | None:
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
        endpoint_id: DeploymentID,
        creator: AutoScalingRuleCreator,
    ) -> AutoScalingRule:
        """Create a new autoscaling rule for an endpoint."""
        return await self._db_source.create_autoscaling_rule(endpoint_id, creator)

    @deployment_repository_resilience.apply()
    async def list_autoscaling_rules(
        self,
        endpoint_id: DeploymentID,
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

    @deployment_repository_resilience.apply()
    async def bulk_delete_autoscaling_rules(
        self,
        rule_ids: list[uuid.UUID],
    ) -> list[uuid.UUID]:
        """Delete multiple autoscaling rules."""
        return await self._db_source.bulk_delete_autoscaling_rules(rule_ids)

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
        endpoint_id: DeploymentID,
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
        vfolder_id: VFolderUUID,
        model_definition_path: str | None,
    ) -> FetchedModelDefinition | None:
        """Fetch and validate the model-definition file from the model vfolder.

        Returns a ``FetchedModelDefinition`` because the file is user-authored
        and may omit optional fields; strict-field validation is deferred to
        the persistence boundary where the merged result is resolved. The
        result also carries the exact candidate path that matched.
        Returns ``None`` when no candidate file exists.
        """
        vfolder_location = await self._db_source.get_vfolder_by_id(vfolder_id)
        if (
            vfolder_location.ownership_type == VFolderOwnershipType.GROUP
            and vfolder_location.usage_mode != VFolderUsageMode.MODEL
        ):
            raise InvalidAPIParameters(
                "Cannot create model service with the project type's vfolder"
            )
        candidates = (
            [model_definition_path]
            if model_definition_path
            else ["model-definition.yaml", "model-definition.yml"]
        )
        return await self._storage_source.fetch_model_definition(vfolder_location, candidates)

    @deployment_repository_resilience.apply()
    async def resolve_vfolder_permissions(
        self,
        vfolder_ids: Sequence[VFolderUUID],
    ) -> dict[VFolderUUID, MountPermission]:
        """Snapshot the stored permission of each vfolder as a ``MountPermission``.

        Used at revision-write time to resolve caller-supplied
        ``MountInfo.mount_perm=None`` (inherit) into a concrete value
        before persisting — see
        ``DeploymentDBSource.resolve_vfolder_permissions`` for the exact
        (minimal) check set.
        """
        return await self._db_source.resolve_vfolder_permissions(vfolder_ids)

    @deployment_repository_resilience.apply()
    async def resolve_user_vfolder_permissions(
        self,
        user_id: uuid.UUID,
        vfolder_ids: Sequence[VFolderUUID],
    ) -> dict[VFolderUUID, MountPermission]:
        """Resolve the requester's effective permission on each vfolder.

        Used at revision-write time to ground the model vfolder mount
        permission into the requesting user's own permission (and to reject
        a request exceeding it) — see
        ``DeploymentDBSource.resolve_user_vfolder_permissions``.
        """
        return await self._db_source.resolve_user_vfolder_permissions(user_id, vfolder_ids)

    @deployment_repository_resilience.apply()
    async def fetch_deployment_config(
        self,
        vfolder_id: VFolderUUID,
    ) -> DeploymentConfig | None:
        """Fetch and resolve the deployment-config file from the model vfolder.

        Storage-side picks the first matching filename from the candidate
        list (new ``deployment-config.yaml`` first, legacy
        ``service-definition.toml`` second) and returns a validated
        ``DeploymentConfigInput``. This repository then resolves the yaml's
        ``image`` / ``architecture`` pair to ``image_id`` so downstream
        callers never handle canonical strings.

        Returns ``None`` when no config file exists.
        """
        vfolder_location = await self._db_source.get_vfolder_by_id(vfolder_id)
        if (
            vfolder_location.ownership_type == VFolderOwnershipType.GROUP
            and vfolder_location.usage_mode != VFolderUsageMode.MODEL
        ):
            raise InvalidAPIParameters(
                "Cannot create model service with the project type's vfolder"
            )

        raw = await self._storage_source.fetch_deployment_config(
            vfolder_location,
            [_DEPLOYMENT_CONFIG_FILENAME, _LEGACY_SERVICE_DEFINITION_FILENAME],
        )
        if raw is None:
            return None

        image_id: ImageID | None = None
        if raw.image is not None and raw.architecture is not None:
            try:
                image_id = await self.get_image_id(
                    ImageIdentifier(canonical=raw.image, architecture=raw.architecture)
                )
            except Exception:
                log.warning(
                    "Failed to resolve image from deployment-config image ref "
                    "{} / {} in vfolder {}; skipping the image layer.",
                    raw.image,
                    raw.architecture,
                    vfolder_id,
                    exc_info=True,
                )

        return DeploymentConfig(
            image_id=image_id,
            resource_slots=raw.resource_slots,
            resource_opts=raw.resource_opts,
            environ=raw.environ,
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
    ) -> Mapping[str, ScalingGroupProxyTarget | None]:
        """Fetch the proxy target URL for a scaling group endpoint."""
        return await self._db_source.fetch_scaling_group_proxy_targets(scaling_group)

    @deployment_repository_resilience.apply()
    async def fetch_auto_scaling_rules_by_deployment_ids(
        self,
        deployment_ids: set[DeploymentID],
    ) -> Mapping[DeploymentID, list[AutoScalingRule]]:
        """Fetch autoscaling rules for multiple deployments."""
        return await self._db_source.fetch_auto_scaling_rules_by_deployment_ids(deployment_ids)

    @deployment_repository_resilience.apply()
    async def fetch_active_routes_by_deployment_ids(
        self,
        deployment_ids: set[DeploymentID],
    ) -> Mapping[DeploymentID, list[RouteInfo]]:
        """Fetch routes for multiple deployments."""
        return await self._db_source.fetch_active_routes_by_deployment_ids(deployment_ids)

    # Route operations

    @deployment_repository_resilience.apply()
    async def search_route_datas(
        self,
        *,
        querier: BatchQuerier,
    ) -> list[RouteData]:
        """Search routes via :class:`BatchQuerier`.

        The caller composes ``querier`` with every filter that applies;
        pagination is part of the querier (use ``NoPagination`` for
        unbounded scans).
        """
        return await self._db_source.search_route_datas(querier=querier)

    async def search_route_datas_with_last_history(
        self,
        *,
        querier: BatchQuerier,
        category: RouteHandlerCategory,
    ) -> list[RouteData]:
        """Search routes with last history per category attached."""
        return await self._db_source.search_route_datas_with_last_history(
            querier=querier, category=category
        )

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
    async def update_route_status_bulk_with_history(
        self,
        batch_updaters: Sequence[BatchUpdater[RoutingRow]],
        bulk_creator: BulkCreator[RouteHistoryRow],
    ) -> int:
        """Update route status and record history in same transaction.

        All batch updates and history creations are executed atomically
        in a single transaction.

        Args:
            batch_updaters: Sequence of BatchUpdaters for status updates
            bulk_creator: BulkCreator containing all history records

        Returns:
            Total number of rows updated
        """
        return await self._db_source.update_route_status_bulk_with_history(
            batch_updaters, bulk_creator
        )

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
    async def update_endpoint_url(
        self,
        endpoint_id: DeploymentID,
        url: str,
    ) -> None:
        """Update a single endpoint's registered URL.

        Args:
            endpoint_id: Endpoint UUID
            url: The registered endpoint URL
        """
        await self._db_source.update_endpoint_url(endpoint_id, url)

    @deployment_repository_resilience.apply()
    async def update_route_sessions(
        self,
        route_session_ids: Mapping[uuid.UUID, SessionId],
    ) -> None:
        """Update session IDs for multiple routes.

        Args:
            route_session_ids: Mapping of route IDs to new session IDs
        """
        await self._db_source.update_route_sessions(route_session_ids)

    @deployment_repository_resilience.apply()
    async def fetch_kernel_connection_info(
        self,
        session_ids: list[SessionId],
    ) -> dict[SessionId, tuple[str, int]]:
        """Fetch kernel_host and inference port for sessions.

        Returns mapping of session_id to (host, port) tuple.
        """
        return await self._db_source.fetch_kernel_connection_info(session_ids)

    @deployment_repository_resilience.apply()
    async def update_route_replica_info(
        self,
        updates: dict[ReplicaID, RouteSessionKernelInfo],
    ) -> None:
        """Update replica_host and replica_port for routes."""
        await self._db_source.update_route_replica_info(updates)

    @deployment_repository_resilience.apply()
    async def fetch_health_check_configs_by_revision_ids(
        self,
        revision_ids: set[DeploymentRevisionID],
    ) -> dict[DeploymentRevisionID, ModelHealthCheck | None]:
        """Fetch health check configurations for revisions."""
        return await self._db_source.fetch_health_check_configs_by_revision_ids(revision_ids)

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
        revision_id: DeploymentRevisionID,
    ) -> DeploymentContext:
        """Fetch all context data needed for session creation from deployment info.

        Args:
            deployment_info: Deployment information
            revision_id: Revision to use for image resolution.

        Returns:
            DeploymentContext: Context data needed for session creation
        """
        return await self._db_source.fetch_deployment_context(deployment_info, revision_id)

    # Auto-scaling operations

    @deployment_repository_resilience.apply()
    async def fetch_metrics_for_autoscaling(
        self,
        deployments: Sequence[DeploymentInfo],
        auto_scaling_rules: Mapping[DeploymentID, Sequence[AutoScalingRule]],
    ) -> AutoScalingMetricsData:
        """Fetch all metrics needed for auto-scaling calculations.

        Args:
            deployments: List of deployments to fetch metrics for
            auto_scaling_rules: Auto-scaling rules by deployment ID

        Returns:
            AutoScalingMetricsData containing all metrics needed for calculations
        """
        # Collect deployment IDs
        deployment_ids = {deployment.id for deployment in deployments}

        # Fetch routes for all deployments
        routes_by_deployment = await self._db_source.fetch_active_routes_by_deployment_ids(
            deployment_ids
        )

        # Determine which metrics we need to fetch based on rules
        metric_requested_sessions: list[SessionId] = []
        metric_requested_kernels: list[KernelId] = []
        metric_requested_deployments: list[DeploymentID] = []
        kernels_by_session_id: dict[SessionId, list[KernelId]] = defaultdict(list)

        for deployment in deployments:
            rules = auto_scaling_rules.get(deployment.id, [])
            for rule in rules:
                if rule.condition.metric_source == AutoScalingMetricSource.KERNEL:
                    # Need to fetch kernel metrics for this deployment's sessions
                    for route in routes_by_deployment.get(deployment.id, []):
                        if route.session_id:
                            metric_requested_sessions.append(route.session_id)
                elif rule.condition.metric_source == AutoScalingMetricSource.INFERENCE_FRAMEWORK:
                    # Need to fetch deployment metrics
                    metric_requested_deployments.append(deployment.id)
                elif rule.condition.metric_source == AutoScalingMetricSource.PROMETHEUS:
                    # Prometheus metrics are fetched in the executor, not from Valkey
                    pass

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
        kernel_statistics_by_id: dict[KernelId, Mapping[str, Any] | None] = {}
        deployment_statistics_by_id: dict[DeploymentID, Mapping[str, Any] | None] = {}

        if metric_requested_kernels:
            kernel_live_stats = await KernelStatistics.batch_load_by_kernel_impl(
                self._valkey_stat,
                cast(list[SessionId], metric_requested_kernels),
            )
            kernel_statistics_by_id = {
                kernel_id: metric
                for kernel_id, metric in zip(
                    metric_requested_kernels, kernel_live_stats, strict=True
                )
            }

        if metric_requested_deployments:
            deployment_live_stats = await EndpointStatistics.batch_load_by_endpoint_impl(
                self._valkey_stat,
                cast(list[uuid.UUID], metric_requested_deployments),
            )
            deployment_statistics_by_id = {
                deployment_id: metric
                for deployment_id, metric in zip(
                    metric_requested_deployments, deployment_live_stats, strict=True
                )
            }

        return AutoScalingMetricsData(
            kernel_statistics=kernel_statistics_by_id,
            deployment_statistics=deployment_statistics_by_id,
            routes_by_deployment=routes_by_deployment,
            kernels_by_session=kernels_by_session_id,
        )

    @deployment_repository_resilience.apply()
    async def calculate_desired_replicas_for_deployment(
        self,
        deployment: DeploymentInfo,
        auto_scaling_rules: Sequence[AutoScalingRule],
        metrics_data: AutoScalingMetricsData,
    ) -> int | None:
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

        current_datetime = datetime.now(UTC)
        current_replica_count = deployment.replica.target_replica_count
        routes = metrics_data.routes_by_deployment.get(deployment.id, [])

        for rule in auto_scaling_rules:
            # Calculate current metric value based on source
            current_value: Decimal | None = None
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
                endpoint_stat = metrics_data.deployment_statistics.get(deployment.id)
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

            elif rule.condition.metric_source == AutoScalingMetricSource.PROMETHEUS:
                # Use pre-fetched Prometheus metrics (populated by executor)
                pre_fetched = metrics_data.prometheus_metrics.get(rule.id)
                if pre_fetched is None:
                    log.warning(
                        "AUTOSCALE(e:{}, rule:{}): skipping - no prometheus metric",
                        deployment.id,
                        rule.id,
                    )
                    continue
                current_value = pre_fetched

            # Evaluate threshold comparison (scale-up and scale-down)
            scale_direction: int = 0  # +1 for scale-out, -1 for scale-in
            if current_value is not None:
                if (
                    rule.condition.scale_up_threshold is not None
                    and current_value > rule.condition.scale_up_threshold
                ):
                    scale_direction = 1
                    should_trigger = True
                    log.debug(
                        "AUTOSCALE(e:{}, rule:{}): {} > {} → scale out",
                        deployment.id,
                        rule.id,
                        current_value,
                        rule.condition.scale_up_threshold,
                    )
                elif (
                    rule.condition.scale_down_threshold is not None
                    and current_value < rule.condition.scale_down_threshold
                ):
                    scale_direction = -1
                    should_trigger = True
                    log.debug(
                        "AUTOSCALE(e:{}, rule:{}): {} < {} → scale in",
                        deployment.id,
                        rule.id,
                        current_value,
                        rule.condition.scale_down_threshold,
                    )
                else:
                    log.debug(
                        "AUTOSCALE(e:{}, rule:{}): {} in range [{}, {}] → no action",
                        deployment.id,
                        rule.id,
                        current_value,
                        rule.condition.scale_down_threshold,
                        rule.condition.scale_up_threshold,
                    )

            if should_trigger:
                # Calculate new replica count
                new_replica_count = max(
                    0, current_replica_count + scale_direction * rule.action.step_size
                )

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
        route_ids: set[ReplicaID],
    ) -> Mapping[ReplicaID, SessionStatus | None]:
        """Fetch session IDs for multiple routes."""
        return await self._db_source.fetch_session_statuses_by_route_ids(route_ids)

    @deployment_repository_resilience.apply()
    async def fetch_route_session_kernel_infos(
        self,
        route_ids: set[ReplicaID],
    ) -> Mapping[ReplicaID, RouteSessionInfo | None]:
        """Fetch session status and kernel connection info for multiple routes.

        Returns:
            Mapping of route_id to RouteSessionInfo:
            - None → route has no session linked
            - RouteSessionInfo(status=TERMINAL, kernel=None) → session terminated
            - RouteSessionInfo(status=RUNNING, kernel=RouteSessionKernelInfo(host, port)) → ready
            - RouteSessionInfo(status=PREPARING, kernel=None) → not yet running
        """
        return await self._db_source.fetch_route_session_kernel_infos(route_ids)

    @deployment_repository_resilience.apply()
    async def fetch_route_connection_infos(
        self,
        *,
        route_querier: BatchQuerier,
    ) -> Mapping[uuid.UUID, list[AppProxyRouteEntry]]:
        """Resolve routing-table entries per endpoint via a caller-composed querier."""
        return await self._db_source.fetch_route_connection_infos(
            route_querier=route_querier,
        )

    @deployment_repository_resilience.apply()
    async def search_deployment_ids(self, *, querier: BatchQuerier) -> list[DeploymentID]:
        """Search deployment ids using ``BatchQuerier``.

        Filter composition is moved to the call site via
        :class:`DeploymentConditions` so the selection criteria
        (e.g. active-lifecycle filter) is explicit.
        """
        return await self._db_source.search_deployment_ids(querier=querier)

    @deployment_repository_resilience.apply()
    async def get_endpoint_id_by_session(
        self,
        session_id: uuid.UUID,
    ) -> uuid.UUID | None:
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
        route_ids: set[ReplicaID],
    ) -> list[RouteServiceDiscoveryInfo]:
        """Fetch service discovery information for routes.

        Args:
            route_ids: Set of route IDs to fetch information for

        Returns:
            List of RouteServiceDiscoveryInfo containing kernel host/port and endpoint details
        """
        return await self._db_source.fetch_route_service_discovery_info(route_ids)

    @deployment_repository_resilience.apply()
    async def load_legacy_model_service_deployment_read_bundle(
        self,
        runtime_variant_id: RuntimeVariantID,
        preset_id: DeploymentPresetID | None,
    ) -> LegacyRevisionCreateReadBundle:
        """Batched read for the legacy model-serving create path.

        Now takes a ``RuntimeVariantID`` — the legacy service layer is
        responsible for resolving name→id via the ResolveRuntimeVariantByName
        action before invoking this flow.
        """
        return await self._db_source.load_legacy_model_service_deployment_read_bundle(
            runtime_variant_id, preset_id
        )

    @deployment_repository_resilience.apply()
    async def load_deployment_revision_read_bundle(
        self,
        runtime_variant_id: RuntimeVariantID,
        preset_id: DeploymentPresetID | None,
    ) -> DeploymentRevisionReadBundle:
        """Batched read for the v2 ``add_revision`` path."""
        return await self._db_source.load_deployment_revision_read_bundle(
            runtime_variant_id, preset_id
        )

    @deployment_repository_resilience.apply()
    async def fetch_revision_required_slot_names(self) -> Iterable[SlotName]:
        """Globally required resource slot names for revision validation."""
        return await self._db_source.fetch_revision_required_slot_names()

    # ========== Deployment Revision Operations ==========

    @deployment_repository_resilience.apply()
    async def create_revision(
        self,
        creator: RBACEntityCreator[DeploymentRevisionRow],
    ) -> ModelRevisionData:
        """Create a new deployment revision."""
        return await self._db_source.create_revision(creator)

    @deployment_repository_resilience.apply()
    async def create_revision_with_next_number(
        self,
        creator: RBACEntityCreator[DeploymentRevisionRow],
        endpoint_id: DeploymentID,
    ) -> ModelRevisionData:
        """Atomically read the latest revision number and create a new revision.

        This avoids the race condition of separate read-then-write operations.
        """
        return await self._db_source.create_revision_with_next_number(creator, endpoint_id)

    @deployment_repository_resilience.apply()
    async def get_revision(
        self,
        revision_id: DeploymentRevisionID,
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
        endpoint_id: DeploymentID,
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
    async def get_latest_revision(
        self,
        endpoint_id: DeploymentID,
    ) -> ModelRevisionData:
        """Get the latest revision (highest ``revision_number``) of a deployment.

        Unlike :meth:`get_current_revision`, this does not consult the primary
        group's ``current_revision_id``: it returns the most recently created
        revision for the endpoint regardless of activation state.

        Raises:
            DeploymentRevisionNotFound: If no revisions exist for the endpoint.
        """
        return await self._db_source.get_latest_revision(endpoint_id)

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
        endpoint_id: DeploymentID,
    ) -> int | None:
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
    async def activate_revision(
        self,
        endpoint_id: DeploymentID,
        revision_id: DeploymentRevisionID,
    ) -> tuple[DeploymentRevisionID | None, bool]:
        """Record the deploy intent and transition lifecycle to DEPLOYING.

        Overrides any previous deploy intent unconditionally;
        leftover routes from the preempted rollout are picked up by
        ``RouteEvictionHandler``'s orphan-revision branch.

        Returns:
            Tuple of (previous_current_revision_id, updated).
            ``updated=False`` means the endpoint row was not found.
        """
        return await self._db_source.activate_revision(endpoint_id, revision_id)

    @deployment_repository_resilience.apply()
    async def prune_old_revisions(
        self,
        endpoint_id: DeploymentID,
        revision_history_limit: int,
    ) -> int:
        """Delete old revisions that exceed the history limit.

        Preserves current_revision and deploying_revision.

        Returns:
            Number of revisions deleted.
        """
        return await self._db_source.prune_old_revisions(endpoint_id, revision_history_limit)

    @deployment_repository_resilience.apply()
    async def upsert_deployment_policy(
        self,
        upserter: Upserter[DeploymentPolicyRow],
    ) -> DeploymentPolicyUpsertResult:
        """Create or update a deployment policy using ON CONFLICT."""
        return await self._db_source.upsert_deployment_policy(upserter)

    @deployment_repository_resilience.apply()
    async def get_deployment_policy(
        self,
        endpoint_id: DeploymentID,
    ) -> DeploymentPolicyData:
        """Get the deployment policy for an endpoint.

        Raises:
            DeploymentPolicyNotFound: If no policy exists for the endpoint.
        """
        return await self._db_source.get_deployment_policy(endpoint_id)

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

    @deployment_repository_resilience.apply()
    async def get_db_now(self) -> datetime:
        """Get current database server time."""
        return await self._db_source.get_db_now()

    # ===================
    # Route operations
    # ===================

    @deployment_repository_resilience.apply()
    async def create_route(
        self,
        creator: RBACEntityCreator[RoutingRow],
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
    async def search_revision_resource_slots(
        self,
        revision_id: DeploymentRevisionID,
        querier: BatchQuerier,
    ) -> tuple[list[tuple[str, Decimal]], int, bool, bool]:
        """Search resource slots allocated to a deployment revision."""
        return await self._db_source.search_revision_resource_slots(revision_id, querier)

    @deployment_repository_resilience.apply()
    async def get_route(
        self,
        route_id: uuid.UUID,
    ) -> RouteInfo | None:
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
        """Search endpoints (modern, light: revision *ids* only)."""
        return await self._db_source.search_endpoints(querier)

    @deployment_repository_resilience.apply()
    async def search_legacy_endpoints(
        self,
        querier: BatchQuerier,
    ) -> DeploymentInfoSearchResult:
        """Search endpoints (legacy, full: includes the current/deploying
        revision data). DO NOT USE in new code — for the REST v1 surface only.
        """
        return await self._db_source.search_legacy_endpoints(querier)

    @deployment_repository_resilience.apply()
    async def search_deployments_in_project(
        self,
        querier: BatchQuerier,
        scope: ProjectDeploymentSearchScope,
    ) -> DeploymentSummarySearchResult:
        """Search endpoints within a project scope with pagination and filtering."""
        return await self._db_source.search_deployments_in_project(querier, scope)

    # ========== Access Token Operations ==========

    @deployment_repository_resilience.apply()
    async def create_access_token(
        self,
        creator: RBACEntityCreator[EndpointTokenRow],
    ) -> EndpointTokenRow:
        """Create a new access token for a model deployment.

        Args:
            creator: RBACEntityCreator containing the EndpointTokenCreatorSpec.

        Returns:
            Created EndpointTokenRow.
        """
        return await self._db_source.create_access_token(creator)

    @deployment_repository_resilience.apply()
    async def get_access_token(
        self,
        token_id: uuid.UUID,
    ) -> ModelDeploymentAccessTokenData:
        """Get a single access token by ID."""
        return await self._db_source.get_access_token(token_id)

    @deployment_repository_resilience.apply()
    async def delete_access_token(
        self,
        token_id: uuid.UUID,
    ) -> bool:
        """Delete an access token."""
        return await self._db_source.delete_access_token(token_id)

    @deployment_repository_resilience.apply()
    async def bulk_delete_access_tokens(
        self,
        token_ids: list[uuid.UUID],
    ) -> list[uuid.UUID]:
        """Delete multiple access tokens."""
        return await self._db_source.bulk_delete_access_tokens(token_ids)

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

    @deployment_repository_resilience.apply()
    async def search_deployment_policies(
        self,
        querier: BatchQuerier,
    ) -> DeploymentPolicySearchResult:
        """Search deployment policies with pagination and filtering.

        Args:
            querier: BatchQuerier containing conditions, orders, and pagination.

        Returns:
            DeploymentPolicySearchResult with items, total_count, and pagination info.
        """
        return await self._db_source.search_deployment_policies(querier)

    @deployment_repository_resilience.apply()
    async def apply_strategy_mutations(
        self,
        rollout: Sequence[RBACEntityCreator[RoutingRow]],
        drain: BatchUpdater[RoutingRow] | None,
        completed_ids: set[DeploymentID],
    ) -> int:
        """Apply route mutations from a strategy evaluation cycle.

        Performs route rollout/drain and revision swap in a single transaction.
        Sub-step transitions are handled by the coordinator via
        ``EndpointLifecycleBatchUpdaterSpec``.

        Returns:
            Number of deployments whose revision was swapped.
        """
        return await self._db_source.apply_strategy_mutations(
            rollout=rollout,
            drain=drain,
            completed_ids=completed_ids,
        )

    @deployment_repository_resilience.apply()
    async def retire_replica_groups_on_destroy(self, deployment_ids: set[DeploymentID]) -> None:
        """Drain the deployments' replica groups and clear their deploying-revision pointer atomically.

        Called from the destroy flow so the reconcile stops provisioning replicas for the gone
        endpoint and no stale group/revision pointer lingers.
        """
        await self._db_source.retire_replica_groups_on_destroy(deployment_ids)

    @deployment_repository_resilience.apply()
    async def clear_deploying_revision(self, deployment_ids: set[DeploymentID]) -> None:
        """Clear deploying_revision and sub_step for rolled-back deployments.

        Called explicitly by ``DeployingRollingBackHandler`` after rollback
        completes — NOT automatically during strategy mutations.
        """
        await self._db_source.clear_deploying_revision(deployment_ids)
