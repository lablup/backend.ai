"""Deployment execution logic."""

import asyncio
import logging
from collections.abc import Sequence
from typing import Any, Coroutine, Optional
from uuid import UUID

from ai.backend.common.clients.http_client.client_pool import (
    ClientKey,
    ClientPool,
)
from ai.backend.common.clients.valkey_client.valkey_stat.client import ValkeyStatClient
from ai.backend.common.config import ModelHealthCheck
from ai.backend.common.types import (
    RuntimeVariant,
)
from ai.backend.logging import BraceStyleAdapter
from ai.backend.manager.clients.wsproxy.client import AppProxyClient
from ai.backend.manager.clients.wsproxy.types import (
    CreateEndpointRequestBody,
    EndpointTagsModel,
    SessionTagsModel,
    TagsModel,
)
from ai.backend.manager.config.provider import ManagerConfigProvider
from ai.backend.manager.data.deployment.types import (
    DeploymentInfo,
    RouteInfo,
    ScaleOutDecision,
)
from ai.backend.manager.data.resource.types import ScalingGroupProxyTarget
from ai.backend.manager.errors.service import ModelDefinitionNotFound
from ai.backend.manager.repositories.deployment.repository import DeploymentRepository
from ai.backend.manager.sokovan.deployment.definition_generator.registry import (
    ModelDefinitionGeneratorRegistry,
    RegistryArgs,
)
from ai.backend.manager.sokovan.scheduling_controller import SchedulingController

from .types import (
    DeploymentExecutionError,
    DeploymentExecutionResult,
)

log = BraceStyleAdapter(logging.getLogger(__name__))

REGISTER_ENDPOINT_TIMEOUT_SEC = 30


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
            RegistryArgs(deployment_repository=self._deployment_repo)
        )

    async def check_pending_deployments(
        self, deployments: Sequence[DeploymentInfo]
    ) -> DeploymentExecutionResult:
        scaling_groups = set(deployment.metadata.resource_group for deployment in deployments)
        scaling_group_targets = await self._deployment_repo.fetch_scaling_group_proxy_targets(
            scaling_groups
        )

        # Collect registration tasks
        registration_tasks: list[Coroutine[Any, Any, str]] = []
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

        # Wait for all tasks to complete
        successful_deployments = []
        errors: list[DeploymentExecutionError] = []
        url_updates: dict[UUID, str] = {}

        if registration_tasks:
            results = await asyncio.gather(*registration_tasks, return_exceptions=True)
            for deployment, result in zip(deployments, results):
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

        # Batch update all endpoint URLs in the database
        if url_updates:
            await self._deployment_repo.update_endpoint_urls_bulk(url_updates)

        return DeploymentExecutionResult(
            successes=successful_deployments,
            errors=errors,
        )

    async def check_ready_deployments_that_need_scaling(
        self, deployments: Sequence[DeploymentInfo]
    ) -> DeploymentExecutionResult:
        endpoint_ids = {deployment.id for deployment in deployments}
        route_map = await self._deployment_repo.fetch_active_routes_by_endpoint_ids(endpoint_ids)
        successes: list[DeploymentInfo] = []
        errors: list[DeploymentExecutionError] = []

        for deployment in deployments:
            routes = route_map[deployment.id]
            if len(routes) != deployment.replica_spec.target_replica_count:
                log.warning(
                    "Deployment {} has mismatched active routes: expected {}, found {}",
                    deployment.id,
                    deployment.replica_spec.target_replica_count,
                    len(routes),
                )
                errors.append(
                    DeploymentExecutionError(
                        deployment_info=deployment,
                        reason="Mismatched active routes",
                        error_detail=f"Expected {deployment.replica_spec.target_replica_count}, found {len(routes)}",
                    )
                )
            else:
                successes.append(deployment)
        return DeploymentExecutionResult(
            successes=successes,
            errors=errors,
        )

    async def scale_deployment(
        self, deployments: Sequence[DeploymentInfo]
    ) -> DeploymentExecutionResult:
        endpoint_ids = {deployment.id for deployment in deployments}
        route_map = await self._deployment_repo.fetch_active_routes_by_endpoint_ids(endpoint_ids)
        scale_outs: list[ScaleOutDecision] = []
        scale_ins: list[RouteInfo] = []
        successes = []
        errors = []
        for deployment in deployments:
            try:
                target_count = deployment.replica_spec.target_replica_count
                routes = route_map[deployment.id]
                if len(routes) < target_count:
                    scale_outs.append(
                        ScaleOutDecision(
                            deployment_info=deployment,
                            new_replica_count=target_count - len(routes),
                        )
                    )
                elif len(routes) > target_count:
                    termination_route_candidates = sorted(
                        routes, key=lambda r: (r.status.termination_priority())
                    )
                    candidates = termination_route_candidates[: len(routes) - target_count]
                    scale_ins.extend(
                        candidates,
                    )
                successes.append(deployment)
            except Exception as e:
                log.warning("Failed to scale deployment {}: {}", deployment.id, e)
                errors.append(
                    DeploymentExecutionError(
                        deployment_info=deployment,
                        reason=str(e),
                        error_detail="Failed to scale deployment",
                    )
                )
        await self._deployment_repo.scale_routes(scale_outs, scale_ins)
        return DeploymentExecutionResult(
            successes=successes,
            errors=errors,
        )

    async def calculate_desired_replicas(
        self, deployments: Sequence[DeploymentInfo]
    ) -> DeploymentExecutionResult:
        endpoint_ids = {deployment.id for deployment in deployments}
        auto_scaling_rules = await self._deployment_repo.fetch_auto_scaling_rules_by_endpoint_ids(
            endpoint_ids
        )

        # Fetch all metrics data upfront
        metrics_data = await self._deployment_repo.fetch_metrics_for_autoscaling(
            deployments, auto_scaling_rules
        )

        successes: list[DeploymentInfo] = []
        skipped: list[DeploymentInfo] = []
        errors: list[DeploymentExecutionError] = []
        desired_replicas_map: dict[UUID, int] = {}

        for deployment in deployments:
            auto_scaling_rule = auto_scaling_rules.get(deployment.id, [])
            if not auto_scaling_rule:
                routes = metrics_data.routes_by_endpoint.get(deployment.id, [])
                if deployment.replica_spec.replica_count != len(routes):
                    desired_replicas_map[deployment.id] = deployment.replica_spec.replica_count
                    successes.append(deployment)
                else:
                    skipped.append(deployment)
                continue
            try:
                # Calculate desired replicas
                desired_replica = (
                    await self._deployment_repo.calculate_desired_replicas_for_deployment(
                        deployment,
                        auto_scaling_rule,
                        metrics_data,
                    )
                )

                if desired_replica is None:
                    log.debug(
                        "No change in desired replicas for deployment {}, skipping", deployment.id
                    )
                    skipped.append(deployment)
                    continue

                desired_replicas_map[deployment.id] = desired_replica
                successes.append(deployment)
            except Exception as e:
                log.warning(
                    "Failed to calculate desired replicas for deployment {}: {}", deployment.id, e
                )
                errors.append(
                    DeploymentExecutionError(
                        deployment_info=deployment,
                        reason=str(e),
                        error_detail="Failed to calculate desired replicas",
                    )
                )
                continue

        # Batch update desired replicas
        if desired_replicas_map:
            await self._deployment_repo.update_desired_replicas_bulk(desired_replicas_map)

        return DeploymentExecutionResult(
            successes=successes,
            skipped=skipped,
            errors=errors,
        )

    async def destroy_deployment(
        self, deployments: Sequence[DeploymentInfo]
    ) -> DeploymentExecutionResult:
        endpoint_ids = {deployment.id for deployment in deployments}
        scaling_groups = {deployment.metadata.resource_group for deployment in deployments}
        routes = await self._deployment_repo.fetch_active_routes_by_endpoint_ids(endpoint_ids)
        proxy_targets = await self._deployment_repo.fetch_scaling_group_proxy_targets(
            scaling_groups
        )
        successes = []
        errors = []
        route_ids = set()
        for route_list in routes.values():
            for route in route_list:
                route_ids.add(route.route_id)
        await self._deployment_repo.mark_terminating_route_status_bulk(route_ids)
        for deployment in deployments:
            proxy_target = proxy_targets[deployment.metadata.resource_group]
            if not proxy_target:
                log.warning(
                    "No proxy target found for scaling group {}, skipping deployment {}",
                    deployment.metadata.resource_group,
                    deployment.id,
                )
                errors.append(
                    DeploymentExecutionError(
                        deployment_info=deployment,
                        reason="No proxy target found",
                        error_detail="Cannot delete endpoint from WSProxy",
                    )
                )
                continue
            try:
                await self._delete_endpoint_from_wsproxy(
                    deployment.id,
                    proxy_target.addr,
                    proxy_target.api_token,
                )
                successes.append(deployment)
            except Exception:
                log.warning(
                    "Failed to delete endpoint {} from WSProxy, it might have been already removed",
                    deployment.id,
                )
                errors.append(
                    DeploymentExecutionError(
                        deployment_info=deployment,
                        reason="Failed to delete endpoint from WSProxy",
                        error_detail="Endpoint might have been already removed",
                    )
                )
            log.info("Deleted endpoint {} from WSProxy", deployment.id)
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
        target_revision = deployment.target_revision()
        if not target_revision:
            raise ModelDefinitionNotFound(f"No target revision for deployment {deployment.id}")
        generator = self._model_definition_generator_registry.get(
            target_revision.execution.runtime_variant
        )
        model_definition = await generator.generate_model_definition(target_revision)
        health_check_config = model_definition.health_check_config()
        if not health_check_config:
            log.debug(
                "No health check configuration found in model definition for deployment {}",
                deployment.id,
            )
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
        existing_url: Optional[str],
        open_to_public: bool,
        health_check_config: Optional[ModelHealthCheck],
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
        return res["endpoint"]

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
