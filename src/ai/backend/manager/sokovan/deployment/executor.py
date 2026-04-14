"""Deployment execution logic."""

import asyncio
import logging
from collections.abc import Mapping, Sequence
from decimal import Decimal, DecimalException
from typing import cast
from uuid import UUID

from ai.backend.common.clients.http_client.client_pool import (
    ClientKey,
    ClientPool,
)
from ai.backend.common.clients.prometheus.client import PrometheusClient
from ai.backend.common.clients.prometheus.preset import LabelMatcher, MetricPreset
from ai.backend.common.clients.valkey_client.valkey_stat.client import ValkeyStatClient
from ai.backend.common.config import ModelHealthCheck
from ai.backend.common.data.permission.types import RBACElementType
from ai.backend.common.exception import (
    BackendAIError,
    FailedToGetMetric,
    PrometheusConnectionError,
)
from ai.backend.common.types import (
    AutoScalingMetricSource,
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
from ai.backend.manager.data.permission.types import RBACElementRef
from ai.backend.manager.data.prometheus_query_preset import PrometheusQueryPresetData
from ai.backend.manager.data.resource.types import ScalingGroupProxyTarget
from ai.backend.manager.errors.deployment import ReplicaCountMismatch
from ai.backend.manager.models.routing import RoutingRow
from ai.backend.manager.models.routing.conditions import RouteConditions
from ai.backend.manager.repositories.base.rbac.entity_creator import RBACEntityCreator
from ai.backend.manager.repositories.base.updater import BatchUpdater
from ai.backend.manager.repositories.deployment.creators import (
    RouteBatchUpdaterSpec,
    RouteCreatorSpec,
)
from ai.backend.manager.repositories.deployment.repository import (
    AutoScalingMetricsData,
    DeploymentRepository,
)
from ai.backend.manager.repositories.prometheus_query_preset.repository import (
    PrometheusQueryPresetRepository,
)
from ai.backend.manager.sokovan.deployment.recorder.context import DeploymentRecorderContext
from ai.backend.manager.sokovan.scheduling_controller import SchedulingController

from .types import (
    DeploymentExecutionError,
    DeploymentExecutionResult,
    DeploymentWithHistory,
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
    _prometheus_client: PrometheusClient
    _preset_repo: PrometheusQueryPresetRepository

    def __init__(
        self,
        deployment_repo: DeploymentRepository,
        scheduling_controller: SchedulingController,
        config_provider: ManagerConfigProvider,
        client_pool: ClientPool,
        valkey_stat: ValkeyStatClient,
        prometheus_client: PrometheusClient,
        preset_repo: PrometheusQueryPresetRepository,
    ) -> None:
        """Initialize the deployment executor."""
        self._deployment_repo = deployment_repo
        self._scheduling_controller = scheduling_controller
        self._config_provider = config_provider
        self._client_pool = client_pool
        self._valkey_stat = valkey_stat
        self._prometheus_client = prometheus_client
        self._preset_repo = preset_repo

    async def check_pending_deployments(
        self, deployments: Sequence[DeploymentWithHistory]
    ) -> DeploymentExecutionResult:
        """Register endpoints in appproxy for deployments that need it."""
        entries: list[tuple[DeploymentWithHistory, UUID]] = []
        pre_skipped: list[DeploymentWithHistory] = []
        for deployment in deployments:
            revision_id = deployment.deployment_info.current_revision_id
            if revision_id is None:
                pre_skipped.append(deployment)
                continue
            entries.append((deployment, revision_id))

        result = await self.register_endpoints_bulk(entries)
        if pre_skipped:
            result = DeploymentExecutionResult(
                successes=result.successes,
                failures=result.failures,
                skipped=[*pre_skipped, *result.skipped],
            )
        return result

    async def register_endpoints_bulk(
        self,
        entries: Sequence[tuple[DeploymentWithHistory, UUID]],
    ) -> DeploymentExecutionResult:
        """Register appproxy endpoints and persist their URLs.

        Entries without a proxy target are reported as ``skipped``.
        Retry-safe: appproxy's endpoint create is idempotent on
        ``endpoint_id``, so a failed URL persist is recovered on the
        next tick.
        """
        if not entries:
            return DeploymentExecutionResult()

        with DeploymentRecorderContext.shared_phase("load_configuration"):
            with DeploymentRecorderContext.shared_step("load_proxy_targets"):
                scaling_groups = {dep.deployment_info.metadata.resource_group for dep, _ in entries}
                scaling_group_targets = (
                    await self._deployment_repo.fetch_scaling_group_proxy_targets(scaling_groups)
                )

        successes: list[DeploymentWithHistory] = []
        failures: list[DeploymentExecutionError] = []
        skipped: list[DeploymentWithHistory] = []

        async def _register_and_persist(
            deployment: DeploymentWithHistory,
            revision_id: UUID,
            target: ScalingGroupProxyTarget,
        ) -> tuple[DeploymentWithHistory, str | None, BaseException | None]:
            info = deployment.deployment_info
            try:
                url = await self.register_endpoint(info, target, revision_id)
                await self._deployment_repo.update_endpoint_url(info.id, url)
            except BaseException as exc:
                return deployment, None, exc
            return deployment, url, None

        tasks: list[tuple[DeploymentWithHistory, UUID, ScalingGroupProxyTarget]] = []
        for deployment, revision_id in entries:
            info = deployment.deployment_info
            target = scaling_group_targets.get(info.metadata.resource_group)
            if not target:
                log.warning(
                    "No proxy target found for scaling group {}, skipping deployment {}",
                    info.metadata.resource_group,
                    info.id,
                )
                skipped.append(deployment)
                continue
            tasks.append((deployment, revision_id, target))

        if not tasks:
            return DeploymentExecutionResult(skipped=skipped)

        results = await asyncio.gather(
            *(_register_and_persist(dep, rev, tgt) for dep, rev, tgt in tasks)
        )

        for deployment, url, error in results:
            dep_id = deployment.deployment_info.id
            if error is not None:
                log.error(
                    "Failed to register endpoint for deployment {}: {}",
                    dep_id,
                    error,
                )
                failures.append(
                    DeploymentExecutionError(
                        deployment_info=deployment,
                        reason=str(error),
                        error_detail="Failed to register endpoint",
                        error_code=_extract_error_code(error),
                    )
                )
            else:
                successes.append(deployment)
                log.info(
                    "Successfully registered endpoint for deployment {} with URL: {}",
                    dep_id,
                    url,
                )

        return DeploymentExecutionResult(
            successes=successes,
            failures=failures,
            skipped=skipped,
        )

    async def check_ready_deployments_that_need_scaling(
        self, deployments: Sequence[DeploymentWithHistory]
    ) -> DeploymentExecutionResult:
        # Phase 1: Load routes
        with DeploymentRecorderContext.shared_phase("load_routes"):
            with DeploymentRecorderContext.shared_step("load_active_routes"):
                endpoint_ids = {dep.deployment_info.id for dep in deployments}
                route_map = await self._deployment_repo.fetch_active_routes_by_endpoint_ids(
                    endpoint_ids
                )

        successes: list[DeploymentWithHistory] = []
        skipped: list[DeploymentWithHistory] = []
        errors: list[DeploymentExecutionError] = []

        # Phase 2: Verify replicas (per-deployment)
        for deployment in deployments:
            # A deployment without a current_revision is either a brand new
            # endpoint that never completed its first rollout or one whose
            # rollout was rolled back. In either case there is nothing to
            # "scale" — there is no revision to create sessions against.
            # Treat it as skipped so no lifecycle transition fires; leaving
            # the handler to attempt scaling would permanently wedge the
            # deployment in SCALING because scale_deployment() would then
            # refuse to act on a None revision id.
            if deployment.deployment_info.current_revision_id is None:
                skipped.append(deployment)
                continue
            try:
                self._verify_deployment_replicas(deployment.deployment_info, route_map)
                successes.append(deployment)
            except ReplicaCountMismatch as e:
                log.warning(
                    "Deployment {} has mismatched active routes: {}",
                    deployment.deployment_info.id,
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
            skipped=skipped,
            failures=errors,
        )

    async def scale_deployment(
        self, deployments: Sequence[DeploymentWithHistory]
    ) -> DeploymentExecutionResult:
        # Phase 1: Load routes
        with DeploymentRecorderContext.shared_phase("load_routes"):
            with DeploymentRecorderContext.shared_step("load_active_routes"):
                endpoint_ids = {dep.deployment_info.id for dep in deployments}
                route_map = await self._deployment_repo.fetch_active_routes_by_endpoint_ids(
                    endpoint_ids
                )

        scale_out_creators: list[RBACEntityCreator[RoutingRow]] = []
        scale_in_route_ids: list[UUID] = []
        successes: list[DeploymentWithHistory] = []
        skipped: list[DeploymentWithHistory] = []
        errors: list[DeploymentExecutionError] = []

        # Phase 2: Evaluate scaling (per-deployment)
        for deployment in deployments:
            info = deployment.deployment_info
            if info.current_revision_id is None:
                skipped.append(deployment)
                continue
            try:
                out_creators, in_route_ids = self._evaluate_deployment_scaling(
                    info, route_map, info.current_revision_id
                )
                if out_creators or in_route_ids:
                    scale_out_creators.extend(out_creators)
                    scale_in_route_ids.extend(in_route_ids)
                    successes.append(deployment)
                else:
                    # No scaling action needed
                    skipped.append(deployment)
            except Exception as e:
                log.warning("Failed to scale deployment {}: {}", deployment.deployment_info.id, e)
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
                "apply_scaling", entity_ids={dep.deployment_info.id for dep in successes}
            ):
                with DeploymentRecorderContext.shared_step("scale_routes"):
                    await self._deployment_repo.scale_routes(scale_out_creators, scale_in_updater)

        return DeploymentExecutionResult(
            successes=successes,
            skipped=skipped,
            failures=errors,
        )

    async def calculate_desired_replicas(
        self, deployments: Sequence[DeploymentWithHistory]
    ) -> DeploymentExecutionResult:
        # Phase 1: Load autoscaling configuration
        with DeploymentRecorderContext.shared_phase("load_autoscaling_config"):
            with DeploymentRecorderContext.shared_step("load_autoscaling_rules"):
                endpoint_ids = {dep.deployment_info.id for dep in deployments}
                auto_scaling_rules = (
                    await self._deployment_repo.fetch_auto_scaling_rules_by_endpoint_ids(
                        endpoint_ids
                    )
                )

            with DeploymentRecorderContext.shared_step("load_metrics"):
                # Fetch all metrics data upfront
                deployment_infos = [dep.deployment_info for dep in deployments]
                metrics_data = await self._deployment_repo.fetch_metrics_for_autoscaling(
                    deployment_infos, auto_scaling_rules
                )

            with DeploymentRecorderContext.shared_step("load_prometheus_metrics"):
                await self._fetch_prometheus_metrics(
                    deployment_infos, auto_scaling_rules, metrics_data
                )

        successes: list[DeploymentWithHistory] = []
        skipped: list[DeploymentWithHistory] = []
        errors: list[DeploymentExecutionError] = []
        desired_replicas_map: dict[UUID, int] = {}

        # Phase 2: Calculate replicas (per-deployment via asyncio.gather).
        # Deployments without a current_revision must be skipped before any
        # desired-replica calculation — otherwise the manual-scaling branch
        # of _calculate_deployment_replicas returns replica_count as "desired"
        # which flips the deployment into SCALING. Once in SCALING,
        # scale_deployment() skips the same deployment because it also has
        # no current_revision to provision sessions against, leaving it
        # permanently wedged. Matching the behaviour of scale_deployment() so
        # the two stay in lock-step.
        deployments_to_calculate: list[DeploymentWithHistory] = []
        for deployment in deployments:
            if deployment.deployment_info.current_revision_id is None:
                skipped.append(deployment)
                continue
            deployments_to_calculate.append(deployment)

        calculation_tasks = [
            self._calculate_deployment_replicas(
                deployment.deployment_info, auto_scaling_rules, metrics_data
            )
            for deployment in deployments_to_calculate
        ]
        results = await asyncio.gather(*calculation_tasks, return_exceptions=True)

        for deployment, result in zip(deployments_to_calculate, results, strict=True):
            dep_id = deployment.deployment_info.id
            if isinstance(result, BaseException):
                log.warning(
                    "Failed to calculate desired replicas for deployment {}: {}",
                    dep_id,
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
                desired_replicas_map[dep_id] = result
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
            failures=errors,
        )

    async def destroy_deployment(
        self, deployments: Sequence[DeploymentWithHistory]
    ) -> DeploymentExecutionResult:
        # Phase 1: Load termination configuration
        with DeploymentRecorderContext.shared_phase("load_termination_config"):
            with DeploymentRecorderContext.shared_step("load_routes"):
                endpoint_ids = {dep.deployment_info.id for dep in deployments}
                routes = await self._deployment_repo.fetch_active_routes_by_endpoint_ids(
                    endpoint_ids
                )

            with DeploymentRecorderContext.shared_step("load_proxy_config"):
                scaling_groups = {
                    dep.deployment_info.metadata.resource_group for dep in deployments
                }
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

        successes: list[DeploymentWithHistory] = []
        errors: list[DeploymentExecutionError] = []

        # Phase 3: Unregister endpoints (per-deployment via asyncio.gather)
        unregister_tasks = [
            self._unregister_endpoint(deployment.deployment_info, proxy_targets)
            for deployment in deployments
        ]
        results = await asyncio.gather(*unregister_tasks, return_exceptions=True)

        for deployment, result in zip(deployments, results, strict=True):
            if isinstance(result, BaseException):
                log.warning(
                    "Failed to unregister endpoint {}: {}",
                    deployment.deployment_info.id,
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
            failures=errors,
        )

    # Private helper methods

    async def register_endpoint(
        self,
        deployment: DeploymentInfo,
        scaling_group_target: ScalingGroupProxyTarget,
        revision_id: UUID,
    ) -> str:
        """Register the deployment's endpoint in appproxy and return its URL.

        Idempotent on ``deployment.id``: repeated calls return the same URL
        without creating a duplicate circuit. The caller is expected to
        persist the returned URL to the ``endpoints`` table.
        """
        pool = DeploymentRecorderContext.current_pool()
        recorder = pool.recorder(deployment.id)

        with recorder.phase("register_endpoint"):
            with recorder.step("check_target_revision"):
                target_revision = deployment.resolve_revision_spec(revision_id)

            with recorder.step("extract_health_check_config"):
                health_check_config = None
                if target_revision.model_definition:
                    health_check_config = target_revision.model_definition.health_check_config()
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
                    runtime_variant=runtime_variant,
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
        revision_id: UUID,
    ) -> tuple[list[RBACEntityCreator[RoutingRow]], list[UUID]]:
        """Evaluate scaling action for a deployment and return creators/route IDs."""
        pool = DeploymentRecorderContext.current_pool()
        recorder = pool.recorder(deployment.id)

        scale_out_creators: list[RBACEntityCreator[RoutingRow]] = []
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
                            revision_id=revision_id,
                        )
                        scale_out_creators.append(
                            RBACEntityCreator(
                                spec=creator_spec,
                                element_type=RBACElementType.ROUTING,
                                scope_ref=RBACElementRef(
                                    element_type=RBACElementType.MODEL_DEPLOYMENT,
                                    element_id=str(deployment.id),
                                ),
                            )
                        )
                elif len(routes) > target_count:
                    termination_route_candidates = sorted(
                        routes, key=lambda r: r.termination_priority
                    )
                    candidates = termination_route_candidates[: len(routes) - target_count]
                    scale_in_route_ids.extend(r.route_id for r in candidates)

        return scale_out_creators, scale_in_route_ids

    async def _fetch_prometheus_metrics(
        self,
        deployments: Sequence[DeploymentInfo],
        auto_scaling_rules: Mapping[UUID, Sequence[AutoScalingRule]],
        metrics_data: AutoScalingMetricsData,
    ) -> None:
        """Fetch Prometheus metrics for rules with PROMETHEUS metric source.

        Results are stored in metrics_data.prometheus_metrics keyed by rule ID.
        """
        prometheus_rules: list[tuple[DeploymentInfo, AutoScalingRule]] = []
        for dep in deployments:
            for rule in auto_scaling_rules.get(dep.id, []):
                if rule.condition.metric_source == AutoScalingMetricSource.PROMETHEUS:
                    prometheus_rules.append((dep, rule))

        if not prometheus_rules:
            return

        # Batch-load unique presets via existing repository
        preset_ids = {
            rule.condition.prometheus_query_preset_id
            for _, rule in prometheus_rules
            if rule.condition.prometheus_query_preset_id is not None
        }
        presets: dict[UUID, PrometheusQueryPresetData] = {}
        for pid in preset_ids:
            try:
                presets[pid] = await self._preset_repo.get_by_id(pid)
            except Exception:
                log.warning("AUTOSCALE: failed to load preset {}", pid)

        # Execute queries concurrently
        tasks = [
            self._fetch_prometheus_metric(dep, rule, presets) for dep, rule in prometheus_rules
        ]
        results = await asyncio.gather(*tasks, return_exceptions=True)

        for (_, rule), result in zip(prometheus_rules, results, strict=True):
            if isinstance(result, BaseException):
                log.warning("AUTOSCALE(rule:{}): prometheus query failed: {}", rule.id, result)
            elif result is not None:
                metrics_data.prometheus_metrics[rule.id] = result

    async def _fetch_prometheus_metric(
        self,
        deployment: DeploymentInfo,
        rule: AutoScalingRule,
        presets: Mapping[UUID, PrometheusQueryPresetData],
    ) -> Decimal | None:
        """Execute a single Prometheus query for an auto-scaling rule.

        Returns the scalar metric value, or None if unavailable.
        """
        preset_id = rule.condition.prometheus_query_preset_id
        if preset_id is None or preset_id not in presets:
            log.warning("AUTOSCALE(rule:{}): preset {} not found", rule.id, preset_id)
            return None

        preset_data: PrometheusQueryPresetData = presets[preset_id]

        # Auto-inject deployment-specific label for scoping
        labels = {"model_service_name": LabelMatcher.exact(deployment.metadata.name)}

        # time_window: preset default → fallback to "5m"
        time_window = preset_data.time_window or "5m"

        metric_preset = MetricPreset(
            template=preset_data.query_template,
            labels=labels,
            window=time_window,
        )

        try:
            response = await self._prometheus_client.query_instant(preset=metric_preset)
        except (PrometheusConnectionError, FailedToGetMetric) as e:
            log.warning(
                "AUTOSCALE(e:{}, rule:{}): prometheus query failed: {}",
                deployment.id,
                rule.id,
                e,
            )
            return None

        if not response.data.result:
            log.debug(
                "AUTOSCALE(e:{}, rule:{}): prometheus query returned empty result",
                deployment.id,
                rule.id,
            )
            return None

        _, value_str = response.data.result[0].values[0]
        try:
            return Decimal(value_str)
        except DecimalException:
            log.warning(
                "AUTOSCALE(e:{}, rule:{}): failed to parse prometheus value '{}'",
                deployment.id,
                rule.id,
                value_str,
            )
            return None

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
