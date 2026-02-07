"""Deployment execution logic."""

import asyncio
import logging
from collections.abc import Coroutine, Mapping, Sequence
from typing import Any, cast
from uuid import UUID

from ai.backend.common.clients.http_client.client_pool import (
    ClientKey,
    ClientPool,
)
from ai.backend.common.clients.valkey_client.valkey_stat.client import ValkeyStatClient
from ai.backend.common.config import ModelHealthCheck
from ai.backend.common.exception import BackendAIError
from ai.backend.common.types import (
    RuntimeVariant,
)
from ai.backend.logging import BraceStyleAdapter
from ai.backend.manager.clients.appproxy.client import AppProxyClient
from ai.backend.manager.clients.appproxy.types import (
    CreateEndpointRequestBody,
    EndpointTagsModel,
    SessionTagsModel,
    TagsModel,
)
from ai.backend.manager.config.provider import ManagerConfigProvider
from ai.backend.manager.data.deployment.scale import AutoScalingRule
from ai.backend.manager.data.deployment.types import (
    DeploymentInfo,
    RouteInfo,
    RouteStatus,
    RouteTrafficStatus,
)
from ai.backend.manager.data.resource.types import ScalingGroupProxyTarget
from ai.backend.manager.errors.deployment import ReplicaCountMismatch
from ai.backend.manager.errors.service import ModelDefinitionNotFound
from ai.backend.manager.models.routing import RoutingRow
from ai.backend.manager.repositories.base import Creator
from ai.backend.manager.repositories.base.updater import BatchUpdater
from ai.backend.manager.repositories.deployment.creators import (
    RouteBatchUpdaterSpec,
    RouteCreatorSpec,
)
from ai.backend.manager.repositories.deployment.options import RouteConditions
from ai.backend.manager.repositories.deployment.repository import (
    AutoScalingMetricsData,
    DeploymentRepository,
)
from ai.backend.manager.sokovan.deployment.definition_generator.registry import (
    ModelDefinitionGeneratorRegistry,
    RegistryArgs,
)
from ai.backend.manager.sokovan.deployment.recorder.context import DeploymentRecorderContext
from ai.backend.manager.sokovan.scheduling_controller import SchedulingController

from .types import (
    DeploymentExecutionError,
    DeploymentExecutionResult,
)

log = BraceStyleAdapter(logging.getLogger(__name__))

REGISTER_ENDPOINT_TIMEOUT_SEC = 30


def _extract_error_code(exception: BaseException) -> str | None:
    """Extract error code from exception if available.

    Args:
        exception: The exception to extract error code from.

    Returns:
        Error code string if exception is BackendAIError, None otherwise.
    """
    if isinstance(exception, BackendAIError):
        return str(exception.error_code())
    return None


class DeploymentExecutor:
    """Executor for deployment operations."""

    _deployment_repo: DeploymentRepository
    _scheduling_controller: SchedulingController
    _config_provider: ManagerConfigProvider
    _client_pool: ClientPool
    _valkey_stat: ValkeyStatClient

    def __init__(
        self,
        deployment_repo: DeploymentRepository,
        scheduling_controller: SchedulingController,
        config_provider: ManagerConfigProvider,
        client_pool: ClientPool,
        valkey_stat: ValkeyStatClient,
    ) -> None:
        """Initialize the deployment executor."""
        self._deployment_repo = deployment_repo
        self._scheduling_controller = scheduling_controller
        self._config_provider = config_provider
        self._client_pool = client_pool
        self._valkey_stat = valkey_stat
        self._model_definition_generator_registry = ModelDefinitionGeneratorRegistry(
            RegistryArgs(
                deployment_repository=self._deployment_repo,
                enable_model_definition_override=self._config_provider.config.deployment.enable_model_definition_override,
            )
        )

    async def check_pending_deployments(
        self, deployments: Sequence[DeploymentInfo]
    ) -> DeploymentExecutionResult:
        # Phase 1: Load configuration
        with DeploymentRecorderContext.shared_phase("load_configuration"):
            with DeploymentRecorderContext.shared_step("load_proxy_targets"):
                scaling_groups = {deployment.metadata.resource_group for deployment in deployments}
                scaling_group_targets = (
                    await self._deployment_repo.fetch_scaling_group_proxy_targets(scaling_groups)
                )

        # Collect registration tasks
        registration_tasks: list[Coroutine[Any, Any, str]] = []
        valid_deployments: list[DeploymentInfo] = []
        for deployment in deployments:
            target_revision = deployment.target_revision()
            if not target_revision:
                log.warning(
                    "Deployment {} has no target revision, skipping",
                    deployment.id,
                )
                continue
            targets = scaling_group_targets[deployment.metadata.resource_group]
            if not targets:
                log.warning(
                    "No proxy target found for scaling group {}, skipping deployment {}",
                    deployment.metadata.resource_group,
                    deployment.id,
                )
                continue
            registration_tasks.append(self._register_endpoint(deployment, targets))
            valid_deployments.append(deployment)

        # Wait for all tasks to complete
        successful_deployments: list[DeploymentInfo] = []
        errors: list[DeploymentExecutionError] = []
        url_updates: dict[UUID, str] = {}

        # Phase 2: Register endpoints (per-deployment phase/step in _register_endpoint)
        if registration_tasks:
            results = await asyncio.gather(*registration_tasks, return_exceptions=True)

            for deployment, result in zip(valid_deployments, results, strict=True):
                if isinstance(result, BaseException):
                    log.error(
                        "Failed to register endpoint for deployment {}: {}",
                        deployment.id,
                        result,
                    )
                    errors.append(
                        DeploymentExecutionError(
                            deployment_info=deployment,
                            reason=str(result),
                            error_detail="Failed to register endpoint",
                            error_code=_extract_error_code(result),
                        )
                    )
                else:
                    # Result is the endpoint URL string returned from _register_endpoint
                    url_updates[deployment.id] = result
                    successful_deployments.append(deployment)
                    log.info(
                        "Successfully registered endpoint for deployment {} with URL: {}",
                        deployment.id,
                        result,
                    )

        # Phase 3: Update endpoint URLs (only for successful deployments)
        if url_updates:
            with DeploymentRecorderContext.shared_phase(
                "update_endpoint_urls", entity_ids=set(url_updates.keys())
            ):
                with DeploymentRecorderContext.shared_step("sync_endpoint_url"):
                    await self._deployment_repo.update_endpoint_urls_bulk(url_updates)

        return DeploymentExecutionResult(
            successes=successful_deployments,
            errors=errors,
        )

    async def check_ready_deployments_that_need_scaling(
        self, deployments: Sequence[DeploymentInfo]
    ) -> DeploymentExecutionResult:
        # Phase 1: Load routes
        with DeploymentRecorderContext.shared_phase("load_routes"):
            with DeploymentRecorderContext.shared_step("load_active_routes"):
                endpoint_ids = {deployment.id for deployment in deployments}
                route_map = await self._deployment_repo.fetch_active_routes_by_endpoint_ids(
                    endpoint_ids
                )

        successes: list[DeploymentInfo] = []
        errors: list[DeploymentExecutionError] = []

        # Phase 2: Verify replicas (per-deployment)
        for deployment in deployments:
            try:
                self._verify_deployment_replicas(deployment, route_map)
                successes.append(deployment)
            except ReplicaCountMismatch as e:
                log.warning(
                    "Deployment {} has mismatched active routes: {}",
                    deployment.id,
                    e,
                )
                errors.append(
                    DeploymentExecutionError(
                        deployment_info=deployment,
                        reason="Mismatched active routes",
                        error_detail=str(e),
                        error_code=_extract_error_code(e),
                    )
                )

        return DeploymentExecutionResult(
            successes=successes,
            errors=errors,
        )

    async def scale_deployment(
        self, deployments: Sequence[DeploymentInfo]
    ) -> DeploymentExecutionResult:
        # Phase 1: Load routes
        with DeploymentRecorderContext.shared_phase("load_routes"):
            with DeploymentRecorderContext.shared_step("load_active_routes"):
                endpoint_ids = {deployment.id for deployment in deployments}
                route_map = await self._deployment_repo.fetch_active_routes_by_endpoint_ids(
                    endpoint_ids
                )

        scale_out_creators: list[Creator[RoutingRow]] = []
        scale_in_route_ids: list[UUID] = []
        successes: list[DeploymentInfo] = []
        skipped: list[DeploymentInfo] = []
        errors: list[DeploymentExecutionError] = []

        # Phase 2: Evaluate scaling (per-deployment)
        for deployment in deployments:
            try:
                out_creators, in_route_ids = self._evaluate_deployment_scaling(
                    deployment, route_map
                )
                if out_creators or in_route_ids:
                    scale_out_creators.extend(out_creators)
                    scale_in_route_ids.extend(in_route_ids)
                    successes.append(deployment)
                else:
                    # No scaling action needed
                    skipped.append(deployment)
            except Exception as e:
                log.warning("Failed to scale deployment {}: {}", deployment.id, e)
                errors.append(
                    DeploymentExecutionError(
                        deployment_info=deployment,
                        reason=str(e),
                        error_detail="Failed to scale deployment",
                        error_code=_extract_error_code(e),
                    )
                )

        # Build BatchUpdater for scale in
        scale_in_updater: BatchUpdater[RoutingRow] | None = None
        if scale_in_route_ids:
            scale_in_updater = BatchUpdater(
                spec=RouteBatchUpdaterSpec(
                    status=RouteStatus.TERMINATING,
                    traffic_ratio=0.0,
                    traffic_status=RouteTrafficStatus.INACTIVE,
                ),
                conditions=[RouteConditions.by_ids(scale_in_route_ids)],
            )

        # Phase 3: Apply scaling (only for successful deployments)
        if scale_out_creators or scale_in_updater:
            with DeploymentRecorderContext.shared_phase(
                "apply_scaling", entity_ids={d.id for d in successes}
            ):
                with DeploymentRecorderContext.shared_step("scale_routes"):
                    await self._deployment_repo.scale_routes(scale_out_creators, scale_in_updater)

        return DeploymentExecutionResult(
            successes=successes,
            skipped=skipped,
            errors=errors,
        )

    async def calculate_desired_replicas(
        self, deployments: Sequence[DeploymentInfo]
    ) -> DeploymentExecutionResult:
        # Phase 1: Load autoscaling configuration
        with DeploymentRecorderContext.shared_phase("load_autoscaling_config"):
            with DeploymentRecorderContext.shared_step("load_autoscaling_rules"):
                endpoint_ids = {deployment.id for deployment in deployments}
                auto_scaling_rules = (
                    await self._deployment_repo.fetch_auto_scaling_rules_by_endpoint_ids(
                        endpoint_ids
                    )
                )

            with DeploymentRecorderContext.shared_step("load_metrics"):
                # Fetch all metrics data upfront
                metrics_data = await self._deployment_repo.fetch_metrics_for_autoscaling(
                    deployments, auto_scaling_rules
                )

        successes: list[DeploymentInfo] = []
        skipped: list[DeploymentInfo] = []
        errors: list[DeploymentExecutionError] = []
        desired_replicas_map: dict[UUID, int] = {}

        # Phase 2: Calculate replicas (per-deployment via asyncio.gather)
        calculation_tasks = [
            self._calculate_deployment_replicas(deployment, auto_scaling_rules, metrics_data)
            for deployment in deployments
        ]
        results = await asyncio.gather(*calculation_tasks, return_exceptions=True)

        for deployment, result in zip(deployments, results, strict=True):
            if isinstance(result, BaseException):
                log.warning(
                    "Failed to calculate desired replicas for deployment {}: {}",
                    deployment.id,
                    result,
                )
                errors.append(
                    DeploymentExecutionError(
                        deployment_info=deployment,
                        reason=str(result),
                        error_detail="Failed to calculate desired replicas",
                        error_code=_extract_error_code(result),
                    )
                )
            elif result is None:
                skipped.append(deployment)
            else:
                desired_replicas_map[deployment.id] = result
                successes.append(deployment)

        # Phase 3: Save scaling decision (only for successful deployments)
        if desired_replicas_map:
            with DeploymentRecorderContext.shared_phase(
                "save_scaling_decision", entity_ids=set(desired_replicas_map.keys())
            ):
                with DeploymentRecorderContext.shared_step("save_target_replicas"):
                    await self._deployment_repo.update_desired_replicas_bulk(desired_replicas_map)

        return DeploymentExecutionResult(
            successes=successes,
            skipped=skipped,
            errors=errors,
        )

    async def destroy_deployment(
        self, deployments: Sequence[DeploymentInfo]
    ) -> DeploymentExecutionResult:
        # Phase 1: Load termination configuration
        with DeploymentRecorderContext.shared_phase("load_termination_config"):
            with DeploymentRecorderContext.shared_step("load_routes"):
                endpoint_ids = {deployment.id for deployment in deployments}
                routes = await self._deployment_repo.fetch_active_routes_by_endpoint_ids(
                    endpoint_ids
                )

            with DeploymentRecorderContext.shared_step("load_proxy_config"):
                scaling_groups = {deployment.metadata.resource_group for deployment in deployments}
                proxy_targets = await self._deployment_repo.fetch_scaling_group_proxy_targets(
                    scaling_groups
                )

        route_ids: set[UUID] = set()
        for route_list in routes.values():
            for route in route_list:
                route_ids.add(route.route_id)

        # Phase 2: Terminate routes
        with DeploymentRecorderContext.shared_phase("terminate_routes"):
            with DeploymentRecorderContext.shared_step("mark_routes_terminating"):
                await self._deployment_repo.mark_terminating_route_status_bulk(route_ids)

        successes: list[DeploymentInfo] = []
        errors: list[DeploymentExecutionError] = []

        # Phase 3: Unregister endpoints (per-deployment via asyncio.gather)
        unregister_tasks = [
            self._unregister_endpoint(deployment, proxy_targets) for deployment in deployments
        ]
        results = await asyncio.gather(*unregister_tasks, return_exceptions=True)

        for deployment, result in zip(deployments, results, strict=True):
            if isinstance(result, BaseException):
                log.warning(
                    "Failed to unregister endpoint {}: {}",
                    deployment.id,
                    result,
                )
                errors.append(
                    DeploymentExecutionError(
                        deployment_info=deployment,
                        reason="Failed to unregister endpoint",
                        error_detail=str(result),
                        error_code=_extract_error_code(result),
                    )
                )
            else:
                successes.append(deployment)

        return DeploymentExecutionResult(
            successes=successes,
            errors=errors,
        )

    # Private helper methods

    async def _register_endpoint(
        self,
        deployment: DeploymentInfo,
        scaling_group_target: ScalingGroupProxyTarget,
    ) -> str:
        pool = DeploymentRecorderContext.current_pool()
        recorder = pool.recorder(deployment.id)

        with recorder.phase("register_endpoint"):
            with recorder.step("check_target_revision"):
                target_revision = deployment.target_revision()
                if not target_revision:
                    raise ModelDefinitionNotFound(
                        f"No target revision for deployment {deployment.id}"
                    )

            with recorder.step("generate_model_definition"):
                model_definition = (
                    await self._model_definition_generator_registry.generate_model_definition(
                        target_revision
                    )
                )
                health_check_config = model_definition.health_check_config()
                if not health_check_config:
                    log.debug(
                        "No health check configuration found in model definition for deployment {}",
                        deployment.id,
                    )

            with recorder.step("register_to_proxy"):
                return await self._create_endpoint_in_proxy(
                    endpoint_id=deployment.id,
                    endpoint_name=deployment.metadata.name,
                    session_owner_id=deployment.metadata.session_owner,
                    project_id=deployment.metadata.project,
                    domain_name=deployment.metadata.domain,
                    runtime_variant=target_revision.execution.runtime_variant,
                    existing_url=deployment.network.url,
                    open_to_public=deployment.network.open_to_public,
                    health_check_config=health_check_config,
                    app_proxy_addr=scaling_group_target.addr,
                    app_proxy_api_token=scaling_group_target.api_token,
                )

    def _load_app_proxy_client(self, address: str, token: str) -> AppProxyClient:
        """Load or create a App Proxy client for the given address."""
        client_session = self._client_pool.load_client_session(
            ClientKey(
                endpoint=address,
                domain="wsproxy",
            )
        )
        return AppProxyClient(client_session, address, token)

    async def _create_endpoint_in_proxy(
        self,
        endpoint_id: UUID,
        endpoint_name: str,
        session_owner_id: UUID,
        project_id: UUID,
        domain_name: str,
        runtime_variant: RuntimeVariant,
        existing_url: str | None,
        open_to_public: bool,
        health_check_config: ModelHealthCheck | None,
        app_proxy_addr: str,
        app_proxy_api_token: str,
    ) -> str:
        """
        Create an endpoint in WSProxy service.

        Args:
            endpoint_id: Endpoint UUID
            endpoint_name: Name of the endpoint
            session_owner_id: UUID of the session owner
            project_id: UUID of the project
            domain_name: Domain name
            runtime_variant: Runtime variant
            existing_url: Existing URL if any
            open_to_public: Public accessibility flag
            health_check_config: Optional health check configuration
            wsproxy_addr: WSProxy service address
            wsproxy_api_token: WSProxy API token

        Returns:
            Response from WSProxy service
        """
        app_proxy_client = self._load_app_proxy_client(app_proxy_addr, app_proxy_api_token)

        # Create request body using Pydantic model
        request_body = CreateEndpointRequestBody(
            version="v2",
            service_name=endpoint_name,
            tags=TagsModel(
                session=SessionTagsModel(
                    user_uuid=str(session_owner_id),
                    group_id=str(project_id),
                    domain_name=domain_name,
                ),
                endpoint=EndpointTagsModel(
                    id=str(endpoint_id),
                    runtime_variant=runtime_variant.value,
                    existing_url=str(existing_url) if existing_url else None,
                ),
            ),
            apps={},
            open_to_public=open_to_public,
            health_check=health_check_config,
        )

        res = await app_proxy_client.create_endpoint(endpoint_id, request_body)
        return cast(str, res["endpoint"])

    async def _delete_endpoint_from_wsproxy(
        self,
        endpoint_id: UUID,
        app_proxy_addr: str,
        app_proxy_api_token: str,
    ) -> None:
        """
        Delete an endpoint from WSProxy service.

        Args:
            endpoint_id: Endpoint UUID to delete
            wsproxy_addr: WSProxy service address
            wsproxy_api_token: WSProxy API token
        """
        app_proxy_client = self._load_app_proxy_client(app_proxy_addr, app_proxy_api_token)
        await app_proxy_client.delete_endpoint(endpoint_id)

    def _verify_deployment_replicas(
        self,
        deployment: DeploymentInfo,
        route_map: Mapping[UUID, Sequence[RouteInfo]],
    ) -> None:
        """Verify that deployment has the expected number of active routes."""
        pool = DeploymentRecorderContext.current_pool()
        recorder = pool.recorder(deployment.id)
        with recorder.phase("verify_replicas"):
            with recorder.step("compare_route_count"):
                routes = route_map[deployment.id]
                if len(routes) != deployment.replica_spec.target_replica_count:
                    raise ReplicaCountMismatch(
                        expected=deployment.replica_spec.target_replica_count,
                        actual=len(routes),
                    )

    def _evaluate_deployment_scaling(
        self,
        deployment: DeploymentInfo,
        route_map: Mapping[UUID, Sequence[RouteInfo]],
    ) -> tuple[list[Creator[RoutingRow]], list[UUID]]:
        """Evaluate scaling action for a deployment and return creators/route IDs."""
        pool = DeploymentRecorderContext.current_pool()
        recorder = pool.recorder(deployment.id)

        scale_out_creators: list[Creator[RoutingRow]] = []
        scale_in_route_ids: list[UUID] = []

        with recorder.phase("evaluate_scaling"):
            with recorder.step("calculate_scale_action"):
                target_count = deployment.replica_spec.target_replica_count
                routes = route_map[deployment.id]
                if len(routes) < target_count:
                    # Build creators for scale out
                    new_replica_count = target_count - len(routes)
                    for _ in range(new_replica_count):
                        creator_spec = RouteCreatorSpec(
                            endpoint_id=deployment.id,
                            session_owner_id=deployment.metadata.session_owner,
                            domain=deployment.metadata.domain,
                            project_id=deployment.metadata.project,
                            revision_id=deployment.current_revision_id,
                        )
                        scale_out_creators.append(Creator(spec=creator_spec))
                elif len(routes) > target_count:
                    termination_route_candidates = sorted(
                        routes, key=lambda r: (r.status.termination_priority())
                    )
                    candidates = termination_route_candidates[: len(routes) - target_count]
                    scale_in_route_ids.extend(r.route_id for r in candidates)

        return scale_out_creators, scale_in_route_ids

    async def _calculate_deployment_replicas(
        self,
        deployment: DeploymentInfo,
        auto_scaling_rules: Mapping[UUID, Sequence[AutoScalingRule]],
        metrics_data: AutoScalingMetricsData,
    ) -> int | None:
        """Calculate desired replicas for a single deployment.

        Returns:
            int: new desired replica count
            None: no change needed (skip)
            Raises exception: on failure
        """
        pool = DeploymentRecorderContext.current_pool()
        recorder = pool.recorder(deployment.id)

        with recorder.phase("calculate_replicas"):
            auto_scaling_rule = auto_scaling_rules.get(deployment.id, [])

            if not auto_scaling_rule:
                with recorder.step("apply_manual_scaling"):
                    routes = metrics_data.routes_by_endpoint.get(deployment.id, [])
                    if deployment.replica_spec.replica_count != len(routes):
                        return deployment.replica_spec.replica_count
                    return None

            with recorder.step("evaluate_autoscaling_rules"):
                desired_replica = (
                    await self._deployment_repo.calculate_desired_replicas_for_deployment(
                        deployment,
                        auto_scaling_rule,
                        metrics_data,
                    )
                )

                if desired_replica is None:
                    log.debug(
                        "No change in desired replicas for deployment {}, skipping",
                        deployment.id,
                    )
                return desired_replica

    async def _unregister_endpoint(
        self,
        deployment: DeploymentInfo,
        proxy_targets: Mapping[str, ScalingGroupProxyTarget | None],
    ) -> None:
        """Unregister an endpoint from the proxy service."""
        pool = DeploymentRecorderContext.current_pool()
        recorder = pool.recorder(deployment.id)

        with recorder.phase("unregister_endpoint"):
            with recorder.step("delete_from_proxy"):
                target = proxy_targets.get(deployment.metadata.resource_group)
                if not target:
                    log.warning(
                        "No proxy target found for scaling group {}, skipping unregister for {}",
                        deployment.metadata.resource_group,
                        deployment.id,
                    )
                    return
                await self._delete_endpoint_from_wsproxy(
                    endpoint_id=deployment.id,
                    app_proxy_addr=target.addr,
                    app_proxy_api_token=target.api_token,
                )
