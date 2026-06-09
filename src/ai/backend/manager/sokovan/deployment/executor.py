"""Deployment execution logic."""

import asyncio
import logging
from collections.abc import Mapping, Sequence
from decimal import Decimal, DecimalException
from uuid import UUID

from ai.backend.common.clients.http_client.client_pool import (
    ClientKey,
    ClientPool,
)
from ai.backend.common.clients.valkey_client.valkey_stat.client import ValkeyStatClient
from ai.backend.common.dto.appproxy_coordinator.v2.endpoint.request import (
    BulkCreateEndpointRequest,
    BulkDeleteEndpointRequest,
)
from ai.backend.common.dto.appproxy_coordinator.v2.endpoint.types import (
    CreateEndpointItem,
    DeleteEndpointItem,
    EndpointTagsModel,
    SessionTagsModel,
    TagsModel,
)
from ai.backend.common.exception import (
    BackendAIError,
    FailedToGetMetric,
    PrometheusConnectionError,
)
from ai.backend.common.identifier.deployment import DeploymentID
from ai.backend.common.identifier.deployment_revision import DeploymentRevisionID
from ai.backend.common.types import (
    AutoScalingMetricSource,
)
from ai.backend.logging import BraceStyleAdapter
from ai.backend.manager.clients.appproxy.client import AppProxyClient
from ai.backend.manager.clients.prometheus.client import PrometheusClient
from ai.backend.manager.config.provider import ManagerConfigProvider
from ai.backend.manager.data.deployment.scale import AutoScalingRule
from ai.backend.manager.data.deployment.types import (
    DeploymentInfo,
)
from ai.backend.manager.data.prometheus_query_preset import PrometheusQueryPresetData
from ai.backend.manager.data.resource.types import ScalingGroupProxyTarget
from ai.backend.manager.errors.deployment import DeploymentRevisionNotFound
from ai.backend.manager.repositories.deployment.repository import (
    AutoScalingMetricsData,
    DeploymentRepository,
)
from ai.backend.manager.repositories.prometheus_query_preset.repository import (
    PrometheusQueryPresetRepository,
)
from ai.backend.manager.repositories.runtime_variant.repository import RuntimeVariantRepository
from ai.backend.manager.sokovan.deployment.recorder.context import DeploymentRecorderContext
from ai.backend.manager.sokovan.scheduling_controller import SchedulingController

from .types import (
    DeploymentExecutionError,
    DeploymentExecutionResult,
    DeploymentWithHistory,
    EndpointRegistrationResult,
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
    _runtime_variant_repo: RuntimeVariantRepository

    def __init__(
        self,
        deployment_repo: DeploymentRepository,
        scheduling_controller: SchedulingController,
        config_provider: ManagerConfigProvider,
        client_pool: ClientPool,
        valkey_stat: ValkeyStatClient,
        prometheus_client: PrometheusClient,
        preset_repo: PrometheusQueryPresetRepository,
        runtime_variant_repo: RuntimeVariantRepository,
    ) -> None:
        """Initialize the deployment executor."""
        self._deployment_repo = deployment_repo
        self._scheduling_controller = scheduling_controller
        self._config_provider = config_provider
        self._client_pool = client_pool
        self._valkey_stat = valkey_stat
        self._prometheus_client = prometheus_client
        self._preset_repo = preset_repo
        self._runtime_variant_repo = runtime_variant_repo

    async def register_endpoints_bulk(
        self,
        entries: Sequence[tuple[DeploymentWithHistory, DeploymentRevisionID]],
    ) -> EndpointRegistrationResult:
        """Register appproxy endpoints and persist their URLs.

        Entries without a proxy target are reported as ``failures`` (a missing
        target is a misconfiguration that retrying will not resolve).
        Entries sharing a proxy target are sent to the coordinator in a
        single bulk call so circuit initialization is batched on the
        AppProxy side. Appproxy's endpoint create is idempotent on
        ``endpoint_id``, so a failed URL persist is recovered on the
        next tick.
        """
        if not entries:
            return EndpointRegistrationResult()

        with DeploymentRecorderContext.shared_phase("load_configuration"):
            with DeploymentRecorderContext.shared_step("load_proxy_targets"):
                scaling_groups = {dep.deployment_info.metadata.resource_group for dep, _ in entries}
                scaling_group_targets = (
                    await self._deployment_repo.fetch_scaling_group_proxy_targets(scaling_groups)
                )

        registered: list[DeploymentWithHistory] = []
        failures: list[DeploymentExecutionError] = []

        # Group entries by proxy target so each target receives one bulk call.
        groups: dict[
            tuple[str, str],
            list[tuple[DeploymentWithHistory, DeploymentRevisionID, ScalingGroupProxyTarget]],
        ] = {}
        for deployment, revision_id in entries:
            info = deployment.deployment_info
            target = scaling_group_targets.get(info.metadata.resource_group)
            if not target:
                log.warning(
                    "No proxy target found for scaling group {} of deployment {}",
                    info.metadata.resource_group,
                    info.id,
                )
                failures.append(
                    DeploymentExecutionError(
                        deployment_info=deployment,
                        reason="No proxy target for scaling group",
                        error_detail=(
                            f"No proxy target for scaling group {info.metadata.resource_group}"
                        ),
                    )
                )
                continue
            groups.setdefault((target.addr, target.api_token), []).append((
                deployment,
                revision_id,
                target,
            ))

        if not groups:
            return EndpointRegistrationResult(failures=failures)

        for (addr, token), group_entries in groups.items():
            await self._dispatch_bulk_register(
                addr,
                token,
                group_entries,
                registered,
                failures,
            )

        return EndpointRegistrationResult(
            registered=registered,
            failures=failures,
        )

    async def _dispatch_bulk_register(
        self,
        addr: str,
        token: str,
        group_entries: Sequence[
            tuple[DeploymentWithHistory, DeploymentRevisionID, ScalingGroupProxyTarget]
        ],
        registered: list[DeploymentWithHistory],
        failures: list[DeploymentExecutionError],
    ) -> None:
        """Build + send one bulk create call for a single proxy target.

        Registered / failures are appended to the shared lists so the
        caller can compose a final ``EndpointRegistrationResult``.
        """
        try:
            items = [
                await self._build_endpoint_item(dep.deployment_info, rev)
                for dep, rev, _ in group_entries
            ]
        except BaseException as exc:
            log.error(
                "Failed to build endpoint items for proxy {}: {}",
                addr,
                exc,
            )
            for deployment, _, _ in group_entries:
                failures.append(
                    DeploymentExecutionError(
                        deployment_info=deployment,
                        reason=str(exc),
                        error_detail="Failed to build endpoint item",
                        error_code=_extract_error_code(exc),
                    )
                )
            return

        client = self._load_app_proxy_client(addr, token)
        try:
            response = await client.create_endpoints_bulk(
                BulkCreateEndpointRequest(endpoints=items)
            )
        except BaseException as exc:
            log.error(
                "Bulk endpoint create failed against proxy {}: {}",
                addr,
                exc,
            )
            for deployment, _, _ in group_entries:
                failures.append(
                    DeploymentExecutionError(
                        deployment_info=deployment,
                        reason=str(exc),
                        error_detail="Bulk endpoint create failed",
                        error_code=_extract_error_code(exc),
                    )
                )
            return

        # Coordinator preserves input order in the response.
        for (deployment, _, _), result_item in zip(group_entries, response.endpoints, strict=False):
            dep_id = deployment.deployment_info.id
            try:
                await self._deployment_repo.update_endpoint_url(dep_id, str(result_item.url))
            except BaseException as exc:
                log.error(
                    "Failed to persist endpoint URL for deployment {}: {}",
                    dep_id,
                    exc,
                )
                failures.append(
                    DeploymentExecutionError(
                        deployment_info=deployment,
                        reason=str(exc),
                        error_detail="Failed to persist endpoint URL",
                        error_code=_extract_error_code(exc),
                    )
                )
                continue
            registered.append(deployment)
            log.info(
                "Successfully registered endpoint for deployment {} with URL: {}",
                dep_id,
                result_item.url,
            )

    async def calculate_desired_replicas(
        self, deployments: Sequence[DeploymentWithHistory]
    ) -> DeploymentExecutionResult:
        # Phase 1: Load autoscaling configuration
        with DeploymentRecorderContext.shared_phase("load_autoscaling_config"):
            with DeploymentRecorderContext.shared_step("load_autoscaling_rules"):
                deployment_ids = {dep.deployment_info.id for dep in deployments}
                auto_scaling_rules = (
                    await self._deployment_repo.fetch_auto_scaling_rules_by_deployment_ids(
                        deployment_ids
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
            if deployment.deployment_info.current_revision is None:
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
        # Phase 1: Load proxy configuration
        deployment_ids = {dep.deployment_info.id for dep in deployments}
        with DeploymentRecorderContext.shared_phase("load_termination_config"):
            with DeploymentRecorderContext.shared_step("load_proxy_config"):
                scaling_groups = {
                    dep.deployment_info.metadata.resource_group for dep in deployments
                }
                proxy_targets = await self._deployment_repo.fetch_scaling_group_proxy_targets(
                    scaling_groups
                )

        # Phase 2: Retire replica groups and clear the deploying-revision pointer in one
        # transaction. Zeroing desired counts makes the scaling reconcile drain existing routes
        # (TERMINATING) and stops it provisioning new replicas for the destroyed endpoints.
        with DeploymentRecorderContext.shared_phase("retire_replica_groups"):
            with DeploymentRecorderContext.shared_step("drain_replica_groups"):
                await self._deployment_repo.retire_replica_groups_on_destroy(deployment_ids)

        successes: list[DeploymentWithHistory] = []
        errors: list[DeploymentExecutionError] = []

        # Phase 3: Group deployments by proxy target and issue one bulk
        # delete per target. Deployments without a proxy target are
        # treated as already unregistered — nothing to do.
        delete_groups: dict[tuple[str, str], list[DeploymentWithHistory]] = {}
        for deployment in deployments:
            info = deployment.deployment_info
            target = proxy_targets.get(info.metadata.resource_group)
            if not target:
                log.warning(
                    "No proxy target found for scaling group {}, skipping unregister for {}",
                    info.metadata.resource_group,
                    info.id,
                )
                successes.append(deployment)
                continue
            delete_groups.setdefault((target.addr, target.api_token), []).append(deployment)

        for (addr, token), group in delete_groups.items():
            await self._dispatch_bulk_unregister(addr, token, group, successes, errors)

        return DeploymentExecutionResult(
            successes=successes,
            failures=errors,
        )

    async def _dispatch_bulk_unregister(
        self,
        addr: str,
        token: str,
        group: Sequence[DeploymentWithHistory],
        successes: list[DeploymentWithHistory],
        errors: list[DeploymentExecutionError],
    ) -> None:
        """Send one bulk delete for deployments sharing a proxy target.

        Per-entry failures reported by the coordinator end up in
        ``errors``; everything else counts as success.
        """
        client = self._load_app_proxy_client(addr, token)
        request = BulkDeleteEndpointRequest(
            endpoints=[DeleteEndpointItem(deployment_id=d.deployment_info.id) for d in group]
        )
        try:
            response = await client.delete_endpoints_bulk(request)
        except BaseException as exc:
            log.warning("Bulk endpoint delete failed against proxy {}: {}", addr, exc)
            for deployment in group:
                errors.append(
                    DeploymentExecutionError(
                        deployment_info=deployment,
                        reason="Failed to unregister endpoint",
                        error_detail=str(exc),
                        error_code=_extract_error_code(exc),
                    )
                )
            return

        for deployment, result_item in zip(group, response.endpoints, strict=True):
            if result_item.success:
                successes.append(deployment)
            else:
                errors.append(
                    DeploymentExecutionError(
                        deployment_info=deployment,
                        reason="Failed to unregister endpoint",
                        error_detail=result_item.error or "unknown",
                        error_code=None,
                    )
                )

    # Private helper methods

    def _load_app_proxy_client(self, address: str, token: str) -> AppProxyClient:
        """Load or create an AppProxy client for the given address."""
        client_session = self._client_pool.load_client_session(
            ClientKey(
                endpoint=address,
                domain="wsproxy",
            )
        )
        return AppProxyClient(client_session, address, token)

    async def _build_endpoint_item(
        self,
        deployment: DeploymentInfo,
        revision_id: DeploymentRevisionID,
    ) -> CreateEndpointItem:
        """Build a :class:`CreateEndpointItem` from a deployment + revision.

        Resolves the runtime variant id to a name at this boundary since
        the AppProxy wire API still keys on the variant name string.
        """
        if (
            deployment.current_revision is not None
            and deployment.current_revision.id == revision_id
        ):
            target_revision = deployment.current_revision
        elif (
            deployment.deploying_revision is not None
            and deployment.deploying_revision.id == revision_id
        ):
            target_revision = deployment.deploying_revision
        else:
            raise DeploymentRevisionNotFound(
                f"Revision {revision_id} not found in deployment {deployment.id}"
            )

        health_check_config = None
        if target_revision.model_definition:
            health_check_config = target_revision.model_definition.health_check_config()
        if not health_check_config:
            log.debug(
                "No health check configuration found in model definition for deployment {}",
                deployment.id,
            )

        variant = await self._runtime_variant_repo.get_by_id(
            target_revision.model_runtime_config.runtime_variant_id
        )

        return CreateEndpointItem(
            deployment_id=deployment.id,
            version="v2",
            service_name=deployment.metadata.name,
            tags=TagsModel(
                session=SessionTagsModel(
                    user_uuid=str(deployment.metadata.session_owner),
                    project_id=str(deployment.metadata.project),
                    domain_name=deployment.metadata.domain,
                ),
                endpoint=EndpointTagsModel(
                    id=str(deployment.id),
                    runtime_variant=variant.name,
                    existing_url=str(deployment.network.url) if deployment.network.url else None,
                ),
            ),
            open_to_public=deployment.network.open_to_public,
            health_check=health_check_config,
        )

    async def _fetch_prometheus_metrics(
        self,
        deployments: Sequence[DeploymentInfo],
        auto_scaling_rules: Mapping[DeploymentID, Sequence[AutoScalingRule]],
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

        # Auto-inject deployment-specific labels declared in preset filter_labels
        available_labels: dict[str, str] = {
            "deployment_id": str(deployment.id),
            "project": str(deployment.metadata.project),
            "session_owner": str(deployment.metadata.session_owner),
        }
        labels = {k: v for k, v in available_labels.items() if k in preset_data.filter_labels}

        # time_window: preset default → fallback to "5m"
        time_window = preset_data.time_window or "5m"

        try:
            response = await self._prometheus_client.execute_preset(
                query_template=preset_data.query_template,
                filter_labels=labels,
                group_labels=[],
                time_window=time_window,
                time_range=None,
            )
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
        auto_scaling_rules: Mapping[DeploymentID, Sequence[AutoScalingRule]],
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
                    routes = metrics_data.routes_by_deployment.get(deployment.id, [])
                    if deployment.replica.replica_count != len(routes):
                        return deployment.replica.replica_count
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
