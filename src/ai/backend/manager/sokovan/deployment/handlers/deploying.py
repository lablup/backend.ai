"""Handler for deploying (strategy-based) deployment operations (BEP-1049).

Splits the deployment lifecycle into an evaluator + per-sub-step handlers:

  - DeploymentStrategyEvaluator: loads policies/routes, runs strategy FSM,
    applies route changes, and groups deployments by sub-step.
  - DeployingInProgressHandler: PROVISIONING / PROGRESSING → DEPLOYING (re-schedule)
    Also performs the revision swap for completed deployments in post_process.
  - DeployingRolledBackHandler: ROLLED_BACK → READY (clear deploying revision)

Each handler returns a concrete next_status() so the coordinator's generic
_handle_status_transitions() records history and transitions lifecycle.
"""

from __future__ import annotations

import logging
from collections import defaultdict
from collections.abc import Sequence
from uuid import UUID

from ai.backend.common.data.model_deployment.types import DeploymentStrategy
from ai.backend.logging import BraceStyleAdapter
from ai.backend.manager.data.deployment.types import (
    DeploymentInfo,
    DeploymentLifecycleStatus,
    DeploymentPolicyData,
    DeploymentStatusTransitions,
    RouteInfo,
    RouteStatus,
    RouteTrafficStatus,
)
from ai.backend.manager.data.model_serving.types import EndpointLifecycle
from ai.backend.manager.defs import LockID
from ai.backend.manager.models.deployment_policy import RollingUpdateSpec
from ai.backend.manager.models.routing import RoutingRow
from ai.backend.manager.repositories.base import Creator
from ai.backend.manager.repositories.base.updater import BatchUpdater
from ai.backend.manager.repositories.deployment.creators import (
    RouteBatchUpdaterSpec,
    RouteCreatorSpec,
)
from ai.backend.manager.repositories.deployment.options import RouteConditions
from ai.backend.manager.sokovan.deployment.deployment_controller import DeploymentController
from ai.backend.manager.sokovan.deployment.executor import DeploymentExecutor
from ai.backend.manager.sokovan.deployment.recorder.context import DeploymentRecorderContext
from ai.backend.manager.sokovan.deployment.route.route_controller import RouteController
from ai.backend.manager.sokovan.deployment.route.types import RouteLifecycleType
from ai.backend.manager.sokovan.deployment.types import (
    CycleEvaluationResult,
    DeploymentExecutionError,
    DeploymentExecutionResult,
    DeploymentLifecycleType,
    DeploymentSubStep,
    EvaluationResult,
)

from .base import DeploymentHandler

log = BraceStyleAdapter(logging.getLogger(__name__))


# ==========================================================================
# Evaluator
# ==========================================================================


class DeploymentStrategyEvaluator:
    """Evaluates DEPLOYING-state deployments and groups them by sub-step.

    Pure evaluation — no processing logic (revision swap etc.).

    Phase 1: Load policies and active routes.
    Phase 2: Run per-deployment strategy FSM → CycleEvaluationResult.
    Phase 3: Apply route changes (scale_out + scale_in) for in-progress items.
    Phase 4: Return EvaluationResult grouped by DeploymentSubStep.
    """

    def __init__(
        self,
        deployment_executor: DeploymentExecutor,
        deployment_controller: DeploymentController,
        route_controller: RouteController,
    ) -> None:
        self._deployment_executor = deployment_executor
        self._deployment_controller = deployment_controller
        self._route_controller = route_controller

    @property
    def lock_id(self) -> LockID | None:
        return LockID.LOCKID_DEPLOYMENT_DEPLOYING

    def target_statuses(self) -> list[EndpointLifecycle]:
        return [EndpointLifecycle.DEPLOYING]

    async def evaluate(self, deployments: Sequence[DeploymentInfo]) -> EvaluationResult:
        """Evaluate one cycle of the deployment strategy for each deployment."""
        log.debug("Evaluating deploying strategies for {} deployments", len(deployments))

        # Phase 1: Load policies and routes
        endpoint_ids = {d.id for d in deployments}
        policy_map = await self._load_policies(deployments)
        route_map = (
            await self._deployment_executor._deployment_repo.fetch_active_routes_by_endpoint_ids(
                endpoint_ids
            )
        )

        groups: dict[DeploymentSubStep, list[DeploymentInfo]] = defaultdict(list)
        completed: list[DeploymentInfo] = []
        skipped: list[DeploymentInfo] = []
        errors: list[DeploymentExecutionError] = []

        scale_out_creators: list[Creator[RoutingRow]] = []
        scale_in_route_ids: list[UUID] = []

        # Phase 2: Evaluate strategy per deployment
        for deployment in deployments:
            try:
                policy = policy_map.get(deployment.id)
                if policy is None:
                    log.warning(
                        "No deployment policy found for deployment {}, skipping",
                        deployment.id,
                    )
                    skipped.append(deployment)
                    continue

                routes = route_map.get(deployment.id, [])

                if policy.strategy == DeploymentStrategy.ROLLING:
                    spec = (
                        policy.strategy_spec
                        if isinstance(policy.strategy_spec, RollingUpdateSpec)
                        else RollingUpdateSpec()
                    )
                    cycle_result = self._rolling_update_evaluate(deployment, routes, spec)
                else:
                    log.warning(
                        "Unsupported deployment strategy {} for deployment {}, skipping",
                        policy.strategy,
                        deployment.id,
                    )
                    skipped.append(deployment)
                    continue

                pool = DeploymentRecorderContext.current_pool()
                recorder = pool.recorder(deployment.id)

                with recorder.phase("strategy_result"):
                    with recorder.step(
                        "determine_sub_step",
                        success_detail=(
                            "completed" if cycle_result.completed else cycle_result.sub_step.value
                        ),
                    ):
                        pass

                if cycle_result.completed:
                    completed.append(deployment)
                else:
                    groups[cycle_result.sub_step].append(deployment)
                    scale_out_creators.extend(cycle_result.scale_out)
                    scale_in_route_ids.extend(cycle_result.scale_in_route_ids)

            except Exception as e:
                log.warning("Failed to evaluate deploying strategy for {}: {}", deployment.id, e)
                errors.append(
                    DeploymentExecutionError(
                        deployment_info=deployment,
                        reason=str(e),
                        error_detail="Failed to evaluate deploying strategy",
                    )
                )

        # Phase 3: Apply route changes (create new routes, terminate old routes)
        if scale_out_creators or scale_in_route_ids:
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

            await self._deployment_executor._deployment_repo.scale_routes(
                scale_out_creators, scale_in_updater
            )

        return EvaluationResult(
            groups=dict(groups),
            completed=completed,
            skipped=skipped,
            errors=errors,
        )

    # ========== Private Helpers ==========

    async def _load_policies(
        self,
        deployments: Sequence[DeploymentInfo],
    ) -> dict[UUID, DeploymentPolicyData]:
        """Load deployment policies for all deployments."""
        policy_map: dict[UUID, DeploymentPolicyData] = {}
        for deployment in deployments:
            try:
                policy = await self._deployment_controller.get_deployment_policy(deployment.id)
                policy_map[deployment.id] = policy
            except Exception:
                log.warning(
                    "Failed to load deployment policy for {}, skipping",
                    deployment.id,
                )
        return policy_map

    # ========== Rolling Update Strategy ==========

    def _rolling_update_evaluate(
        self,
        deployment: DeploymentInfo,
        routes: Sequence[RouteInfo],
        spec: RollingUpdateSpec,
    ) -> CycleEvaluationResult:
        """Evaluate one cycle of the rolling update strategy."""
        pool = DeploymentRecorderContext.current_pool()
        recorder = pool.recorder(deployment.id)

        deploying_revision = deployment.deploying_revision_id
        desired_replicas = deployment.replica_spec.target_replica_count

        with recorder.phase("rolling_update_evaluate"):
            # Classify routes into old and new by revision
            with recorder.step("classify_routes"):
                new_routes = [
                    r
                    for r in routes
                    if r.revision_id == deploying_revision and r.status.is_active()
                ]
                old_routes = [
                    r
                    for r in routes
                    if r.revision_id != deploying_revision and r.status.is_active()
                ]

                new_provisioning = [r for r in new_routes if r.status == RouteStatus.PROVISIONING]
                new_healthy = [r for r in new_routes if r.status == RouteStatus.HEALTHY]
                old_active = old_routes  # All active old routes

                log.debug(
                    "Rolling update for {}: new_healthy={}, new_prov={}, old_active={}, desired={}",
                    deployment.id,
                    len(new_healthy),
                    len(new_provisioning),
                    len(old_active),
                    desired_replicas,
                )

            # Step 1: If any new routes are still PROVISIONING, wait
            if new_provisioning:
                with recorder.step("wait_provisioning"):
                    log.debug(
                        "Rolling update for {}: waiting for {} provisioning routes",
                        deployment.id,
                        len(new_provisioning),
                    )
                return CycleEvaluationResult(sub_step=DeploymentSubStep.PROVISIONING)

            # Step 2: Check completion — no old routes and new healthy >= desired
            with recorder.step("check_completion"):
                if not old_active and len(new_healthy) >= desired_replicas:
                    log.info(
                        "Rolling update completed for deployment {}: {} healthy routes",
                        deployment.id,
                        len(new_healthy),
                    )
                    return CycleEvaluationResult(
                        sub_step=DeploymentSubStep.PROGRESSING,
                        completed=True,
                    )

            # Step 3: Calculate surge/unavailable and create/terminate routes
            with recorder.step("calculate_surge"):
                max_surge = spec.max_surge
                max_unavailable = spec.max_unavailable

                max_total = desired_replicas + max_surge
                min_available = max(0, desired_replicas - max_unavailable)

                total_active = len(new_routes) + len(old_active)

                # How many new routes we can create
                can_create = max(0, max_total - total_active)
                need_create = max(0, desired_replicas - len(new_healthy) - len(new_provisioning))
                to_create = min(can_create, need_create)

                # How many old routes we can terminate
                healthy_count = len(new_healthy) + len(old_active)
                can_terminate = max(0, healthy_count - min_available)
                to_terminate = min(can_terminate, len(old_active))

                log.debug(
                    "Rolling update for {}: to_create={}, to_terminate={} "
                    "(max_total={}, min_available={}, total_active={})",
                    deployment.id,
                    to_create,
                    to_terminate,
                    max_total,
                    min_available,
                    total_active,
                )

            # Build route creation specs
            scale_out_creators: list[Creator[RoutingRow]] = []
            scale_in_route_ids: list[UUID] = []

            with recorder.step("build_route_changes"):
                for _ in range(to_create):
                    creator_spec = RouteCreatorSpec(
                        endpoint_id=deployment.id,
                        session_owner_id=deployment.metadata.session_owner,
                        domain=deployment.metadata.domain,
                        project_id=deployment.metadata.project,
                        revision_id=deploying_revision,
                        traffic_status=RouteTrafficStatus.ACTIVE,
                    )
                    scale_out_creators.append(Creator(spec=creator_spec))

                # Terminate old routes (lowest termination priority first)
                if to_terminate > 0:
                    sorted_old = sorted(old_active, key=lambda r: r.status.termination_priority())
                    scale_in_route_ids.extend(r.route_id for r in sorted_old[:to_terminate])

        return CycleEvaluationResult(
            sub_step=DeploymentSubStep.PROGRESSING,
            scale_out=scale_out_creators,
            scale_in_route_ids=scale_in_route_ids,
        )


# ==========================================================================
# Sub-step Handlers
# ==========================================================================


class DeployingInProgressHandler(DeploymentHandler):
    """Base handler for PROVISIONING / PROGRESSING sub-steps.

    Route changes have already been applied by the evaluator.
    Returns DEPLOYING → DEPLOYING so the coordinator records a history entry
    and the lifecycle remains in DEPLOYING for the next cycle.

    Subclasses hard-code their specific sub-step in next_status/status_transitions.
    """

    def __init__(
        self,
        deployment_executor: DeploymentExecutor,
        deployment_controller: DeploymentController,
        route_controller: RouteController,
    ) -> None:
        self._deployment_executor = deployment_executor
        self._deployment_controller = deployment_controller
        self._route_controller = route_controller

    @property
    def lock_id(self) -> LockID | None:
        return LockID.LOCKID_DEPLOYMENT_DEPLOYING

    @classmethod
    def target_statuses(cls) -> list[EndpointLifecycle]:
        return [EndpointLifecycle.DEPLOYING]

    def failure_status(self) -> DeploymentLifecycleStatus | None:
        return None

    async def execute(self, deployments: Sequence[DeploymentInfo]) -> DeploymentExecutionResult:
        """Route changes already applied by evaluator; just mark as success."""
        return DeploymentExecutionResult(successes=list(deployments))

    async def post_process(self, result: DeploymentExecutionResult) -> None:
        """Re-schedule deploying lifecycle, trigger route provisioning, and swap revisions."""
        if result.successes:
            log.info(
                "Deploying in progress for {} deployments, re-scheduling",
                len(result.successes),
            )
            await self._deployment_controller.mark_lifecycle_needed(
                DeploymentLifecycleType.DEPLOYING
            )
        await self._route_controller.mark_lifecycle_needed(RouteLifecycleType.PROVISIONING)

        # Swap revisions for completed deployments (set by coordinator from EvaluationResult)
        if result.completed:
            swap_ids = [d.id for d in result.completed if d.deploying_revision_id is not None]
            if swap_ids:
                log.info("Swapping revisions for {} completed deployments", len(swap_ids))
                await self._deployment_executor._deployment_repo.complete_deployment_revision_swap(
                    swap_ids
                )


class DeployingProvisioningHandler(DeployingInProgressHandler):
    """Handler for PROVISIONING sub-step."""

    @classmethod
    def name(cls) -> str:
        return "deploying-provisioning"

    def next_status(self) -> DeploymentLifecycleStatus | None:
        return DeploymentLifecycleStatus(
            lifecycle=EndpointLifecycle.DEPLOYING,
            sub_status=DeploymentSubStep.PROVISIONING,
        )

    def status_transitions(self) -> DeploymentStatusTransitions:
        return DeploymentStatusTransitions(
            success=DeploymentLifecycleStatus(
                lifecycle=EndpointLifecycle.DEPLOYING,
                sub_status=DeploymentSubStep.PROVISIONING,
            ),
            failure=None,
        )


class DeployingProgressingHandler(DeployingInProgressHandler):
    """Handler for PROGRESSING sub-step."""

    @classmethod
    def name(cls) -> str:
        return "deploying-progressing"

    def next_status(self) -> DeploymentLifecycleStatus | None:
        return DeploymentLifecycleStatus(
            lifecycle=EndpointLifecycle.DEPLOYING,
            sub_status=DeploymentSubStep.PROGRESSING,
        )

    def status_transitions(self) -> DeploymentStatusTransitions:
        return DeploymentStatusTransitions(
            success=DeploymentLifecycleStatus(
                lifecycle=EndpointLifecycle.DEPLOYING,
                sub_status=DeploymentSubStep.PROGRESSING,
            ),
            failure=None,
        )


class DeployingRolledBackHandler(DeploymentHandler):
    """Handler for ROLLED_BACK sub-step.

    Clears deploying_revision (sets to NULL) and transitions
    DEPLOYING → READY via the coordinator's generic path.
    """

    def __init__(
        self,
        deployment_executor: DeploymentExecutor,
        deployment_controller: DeploymentController,
    ) -> None:
        self._deployment_executor = deployment_executor
        self._deployment_controller = deployment_controller

    @classmethod
    def name(cls) -> str:
        return "deploying-rolled-back"

    @property
    def lock_id(self) -> LockID | None:
        return LockID.LOCKID_DEPLOYMENT_DEPLOYING

    @classmethod
    def target_statuses(cls) -> list[EndpointLifecycle]:
        return [EndpointLifecycle.DEPLOYING]

    def next_status(self) -> DeploymentLifecycleStatus | None:
        return DeploymentLifecycleStatus(
            lifecycle=EndpointLifecycle.READY,
            sub_status=DeploymentSubStep.ROLLED_BACK,
        )

    def failure_status(self) -> DeploymentLifecycleStatus | None:
        return None

    def status_transitions(self) -> DeploymentStatusTransitions:
        return DeploymentStatusTransitions(
            success=DeploymentLifecycleStatus(
                lifecycle=EndpointLifecycle.READY,
                sub_status=DeploymentSubStep.ROLLED_BACK,
            ),
            failure=None,
        )

    async def execute(self, deployments: Sequence[DeploymentInfo]) -> DeploymentExecutionResult:
        """Clear deploying_revision for rolled-back deployments."""
        await self._clear_deploying_revision(deployments)
        return DeploymentExecutionResult(successes=list(deployments))

    async def post_process(self, result: DeploymentExecutionResult) -> None:
        pass

    async def _clear_deploying_revision(
        self,
        deployments: Sequence[DeploymentInfo],
    ) -> None:
        """Clear deploying_revision (set to NULL) for rolled-back deployments."""
        clear_ids = [d.id for d in deployments if d.deploying_revision_id is not None]
        if not clear_ids:
            return
        await self._deployment_executor._deployment_repo.clear_deploying_revision(clear_ids)
