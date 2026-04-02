"""Handlers for DEPLOYING sub-steps (BEP-1049).

Three DEPLOYING handlers are registered in the coordinator's HandlerRegistry:

- **DeployingProvisioningHandler**: Creates new-revision routes and waits for
  them to become HEALTHY; advances to AWAITING_PROMOTION on success.
- **DeployingAwaitingPromotionHandler**: All new routes healthy; waiting for
  promotion trigger (manual approval or delay timer); advances to READY on
  COMPLETED, or ROLLING_BACK on timeout/give_up.
- **DeployingRollingBackHandler**: Clears ``deploying_revision`` and
  transitions directly to READY.

Sub-step flow::

    PROVISIONING ──(success)──▸ AWAITING_PROMOTION
         │                           │
         │ (expired/give_up)  ┌──────┴──────┐
         ▼                    ▼              ▼
    ROLLING_BACK         COMPLETED      ROLLING_BACK
         │                    │              │
         │ (success)          │ (success)    │ (success)
         ▼                    ▼              ▼
       READY                READY          READY

The evaluator determines sub-step assignments and route mutations;
the applier persists them to DB atomically.  Each handler classifies
deployments into successes (transition forward), need_retry (route mutations
with history logged), and skipped (no change — waiting).
"""

from __future__ import annotations

import logging
import uuid
from collections.abc import Sequence
from datetime import UTC, datetime
from typing import override
from uuid import UUID

from ai.backend.logging import BraceStyleAdapter
from ai.backend.manager.data.deployment.types import (
    DeploymentInfo,
    DeploymentLifecycleStatus,
    DeploymentLifecycleSubStep,
    DeploymentStatusTransitions,
    RouteHealthStatus,
    RouteStatus,
)
from ai.backend.manager.data.model_serving.types import EndpointLifecycle
from ai.backend.manager.defs import LockID
from ai.backend.manager.models.deployment_policy import BlueGreenSpec
from ai.backend.manager.models.routing.conditions import RouteConditions
from ai.backend.manager.repositories.base import BatchQuerier, NoPagination
from ai.backend.manager.repositories.deployment.repository import DeploymentRepository
from ai.backend.manager.sokovan.deployment.deployment_controller import DeploymentController
from ai.backend.manager.sokovan.deployment.executor import DeploymentExecutor
from ai.backend.manager.sokovan.deployment.route.route_controller import RouteController
from ai.backend.manager.sokovan.deployment.route.types import RouteLifecycleType
from ai.backend.manager.sokovan.deployment.strategy.applier import (
    StrategyResultApplier,
)
from ai.backend.manager.sokovan.deployment.strategy.evaluator import (
    DeploymentStrategyEvaluator,
)
from ai.backend.manager.sokovan.deployment.types import (
    DeploymentExecutionError,
    DeploymentExecutionResult,
    DeploymentLifecycleType,
    DeploymentWithHistory,
)

from .base import DeploymentHandler

log = BraceStyleAdapter(logging.getLogger(__name__))


# ---------------------------------------------------------------------------
# DEPLOYING sub-step handlers
# ---------------------------------------------------------------------------


class DeployingProvisioningHandler(DeploymentHandler):
    """Handler for the DEPLOYING / PROVISIONING sub-step.

    New-revision routes are being created; waiting for them to become HEALTHY.
    The evaluator assigns sub-steps; when all new routes are healthy the
    deployment advances to AWAITING_PROMOTION (success), otherwise it stays in
    PROVISIONING (skipped — no state transition).
    """

    def __init__(
        self,
        deployment_controller: DeploymentController,
        route_controller: RouteController,
        evaluator: DeploymentStrategyEvaluator,
        applier: StrategyResultApplier,
        deployment_executor: DeploymentExecutor,
        deployment_repo: DeploymentRepository,
    ) -> None:
        self._deployment_controller = deployment_controller
        self._route_controller = route_controller
        self._evaluator = evaluator
        self._applier = applier
        self._deployment_executor = deployment_executor
        self._deployment_repo = deployment_repo

    @classmethod
    @override
    def name(cls) -> str:
        return "deploying-provisioning"

    @property
    @override
    def lock_id(self) -> LockID | None:
        return LockID.LOCKID_DEPLOYMENT_DEPLOYING

    @classmethod
    @override
    def target_statuses(cls) -> list[DeploymentLifecycleStatus]:
        return [
            DeploymentLifecycleStatus(
                lifecycle=EndpointLifecycle.DEPLOYING,
                sub_step=DeploymentLifecycleSubStep.DEPLOYING_PROVISIONING,
            ),
        ]

    @classmethod
    @override
    def status_transitions(cls) -> DeploymentStatusTransitions:
        return DeploymentStatusTransitions(
            success=DeploymentLifecycleStatus(
                lifecycle=EndpointLifecycle.DEPLOYING,
                sub_step=DeploymentLifecycleSubStep.DEPLOYING_AWAITING_PROMOTION,
            ),
            expired=DeploymentLifecycleStatus(
                lifecycle=EndpointLifecycle.DEPLOYING,
                sub_step=DeploymentLifecycleSubStep.DEPLOYING_ROLLING_BACK,
            ),
            give_up=DeploymentLifecycleStatus(
                lifecycle=EndpointLifecycle.DEPLOYING,
                sub_step=DeploymentLifecycleSubStep.DEPLOYING_ROLLING_BACK,
            ),
        )

    async def _ensure_endpoints_registered(
        self, deployments: Sequence[DeploymentWithHistory]
    ) -> set[UUID]:
        """Register endpoints for deployments that entered DEPLOYING via
        ActivateRevision and therefore skipped ``check_pending``.

        Returns IDs whose registration failed so the caller can exclude
        them from this tick's route provisioning.
        """
        entries: list[tuple[DeploymentWithHistory, UUID]] = []
        for deployment in deployments:
            info = deployment.deployment_info
            if info.network.url:
                continue
            if info.deploying_revision_id is None:
                continue
            entries.append((deployment, info.deploying_revision_id))

        if not entries:
            return set()

        result = await self._deployment_executor.register_endpoints_bulk(entries)
        return {error.deployment_info.deployment_info.id for error in result.failures}

    @override
    async def execute(
        self, deployments: Sequence[DeploymentWithHistory]
    ) -> DeploymentExecutionResult:
        # BA-5557: pre-register endpoints for deployments that bypassed
        # check_pending via ActivateRevision. On failure, drop them from
        # this tick so they retry next cycle; pre-registered deployments
        # keep flowing into route provisioning.
        try:
            failed_registration_ids = await self._ensure_endpoints_registered(deployments)
        except Exception as exc:
            log.exception("Pre-registration step failed: {}", exc)
            failed_registration_ids = {
                deployment.deployment_info.id
                for deployment in deployments
                if not deployment.deployment_info.network.url
                and deployment.deployment_info.deploying_revision_id is not None
            }
        if failed_registration_ids:
            deployments = [
                deployment
                for deployment in deployments
                if deployment.deployment_info.id not in failed_registration_ids
            ]

        deployment_infos = [deployment.deployment_info for deployment in deployments]
        deployment_map = {deployment.deployment_info.id: deployment for deployment in deployments}

        summary = await self._evaluator.evaluate(deployment_infos)
        await self._applier.apply(summary)

        successes: list[DeploymentWithHistory] = []
        skipped: list[DeploymentWithHistory] = []

        for deployment in deployments:
            endpoint_id = deployment.deployment_info.id
            assigned = summary.assignments.get(endpoint_id)
            if assigned is None:
                continue
            if assigned == DeploymentLifecycleSubStep.DEPLOYING_AWAITING_PROMOTION:
                successes.append(deployment)
            else:
                skipped.append(deployment)

        errors = [
            DeploymentExecutionError(
                deployment_info=deployment_map[evaluation_error.deployment.id],
                reason=evaluation_error.reason,
                error_detail=evaluation_error.reason,
            )
            for evaluation_error in summary.errors
            if evaluation_error.deployment.id in deployment_map
        ]

        return DeploymentExecutionResult(successes=successes, failures=errors, skipped=skipped)

    @override
    async def post_process(self, result: DeploymentExecutionResult) -> None:
        await self._deployment_controller.mark_lifecycle_needed(
            DeploymentLifecycleType.DEPLOYING,
            sub_step=DeploymentLifecycleSubStep.DEPLOYING_PROVISIONING,
        )
        await self._route_controller.mark_lifecycle_needed(RouteLifecycleType.PROVISIONING)


class DeployingAwaitingPromotionHandler(DeploymentHandler):
    """Handler for DEPLOYING / AWAITING_PROMOTION.

    Checks whether auto-promotion conditions are met
    (``auto_promote=True`` + delay elapsed).  If so, executes
    promote/drain via the repository and returns *success* so the
    coordinator transitions to READY.

    Otherwise the deployment is *skipped* and stays in
    AWAITING_PROMOTION until the user calls ``promote_deployment``
    or the deploying timeout expires.
    """

    def __init__(
        self,
        deployment_controller: DeploymentController,
        deployment_repository: DeploymentRepository,
    ) -> None:
        self._deployment_controller = deployment_controller
        self._deployment_repository = deployment_repository

    @classmethod
    @override
    def name(cls) -> str:
        return "deploying-awaiting-promotion"

    @property
    @override
    def lock_id(self) -> LockID | None:
        return LockID.LOCKID_DEPLOYMENT_DEPLOYING

    @classmethod
    @override
    def target_statuses(cls) -> list[DeploymentLifecycleStatus]:
        return [
            DeploymentLifecycleStatus(
                lifecycle=EndpointLifecycle.DEPLOYING,
                sub_step=DeploymentLifecycleSubStep.DEPLOYING_AWAITING_PROMOTION,
            ),
        ]

    @classmethod
    @override
    def status_transitions(cls) -> DeploymentStatusTransitions:
        ready = DeploymentLifecycleStatus(
            lifecycle=EndpointLifecycle.READY,
            sub_step=None,
        )
        rolling_back = DeploymentLifecycleStatus(
            lifecycle=EndpointLifecycle.DEPLOYING,
            sub_step=DeploymentLifecycleSubStep.DEPLOYING_ROLLING_BACK,
        )
        return DeploymentStatusTransitions(
            success=ready,
            expired=rolling_back,
            give_up=rolling_back,
        )

    @override
    async def execute(
        self, deployments: Sequence[DeploymentWithHistory]
    ) -> DeploymentExecutionResult:
        successes: list[DeploymentWithHistory] = []
        skipped: list[DeploymentWithHistory] = []

        for deployment in deployments:
            info = deployment.deployment_info
            policy = info.policy
            if policy is None or not isinstance(policy.strategy_spec, BlueGreenSpec):
                skipped.append(deployment)
                continue

            spec: BlueGreenSpec = policy.strategy_spec
            if not spec.auto_promote:
                skipped.append(deployment)
                continue

            if spec.promote_delay_seconds > 0 and deployment.phase_started_at is not None:
                elapsed = (datetime.now(UTC) - deployment.phase_started_at).total_seconds()
                if elapsed < spec.promote_delay_seconds:
                    skipped.append(deployment)
                    continue

            promote_route_ids, drain_route_ids = await self._classify_routes(info)
            await self._deployment_repository.promote_deployment(
                deployment_id=info.id,
                promote_route_ids=promote_route_ids,
                drain_route_ids=drain_route_ids,
            )
            log.info("deployment {}: auto-promoted", info.id)
            successes.append(deployment)

        return DeploymentExecutionResult(successes=successes, skipped=skipped)

    async def _classify_routes(
        self,
        info: DeploymentInfo,
    ) -> tuple[list[uuid.UUID], list[uuid.UUID]]:
        route_search = await self._deployment_repository.search_routes(
            BatchQuerier(
                pagination=NoPagination(),
                conditions=[
                    RouteConditions.by_endpoint_ids({info.id}),
                    RouteConditions.exclude_statuses([RouteStatus.TERMINATED]),
                ],
            )
        )
        promote_route_ids: list[uuid.UUID] = []
        drain_route_ids: list[uuid.UUID] = []
        for route in route_search.items:
            if route.revision_id == info.deploying_revision_id:
                if route.health_status == RouteHealthStatus.HEALTHY:
                    promote_route_ids.append(route.route_id)
            elif route.status.is_active():
                drain_route_ids.append(route.route_id)
        return promote_route_ids, drain_route_ids

    @override
    async def post_process(self, result: DeploymentExecutionResult) -> None:
        await self._deployment_controller.mark_lifecycle_needed(
            DeploymentLifecycleType.DEPLOYING,
            sub_step=DeploymentLifecycleSubStep.DEPLOYING_AWAITING_PROMOTION,
        )


class DeployingRollingBackHandler(DeploymentHandler):
    """Handler for DEPLOYING / ROLLING_BACK sub-step.

    Clears ``deploying_revision`` and transitions to READY,
    completing the rollback process.
    """

    def __init__(
        self,
        deployment_controller: DeploymentController,
        route_controller: RouteController,
        deployment_repo: DeploymentRepository,
    ) -> None:
        self._deployment_controller = deployment_controller
        self._route_controller = route_controller
        self._deployment_repo = deployment_repo

    @classmethod
    @override
    def name(cls) -> str:
        return "deploying-rolling-back"

    @property
    @override
    def lock_id(self) -> LockID | None:
        return LockID.LOCKID_DEPLOYMENT_DEPLOYING

    @classmethod
    @override
    def target_statuses(cls) -> list[DeploymentLifecycleStatus]:
        return [
            DeploymentLifecycleStatus(
                lifecycle=EndpointLifecycle.DEPLOYING,
                sub_step=DeploymentLifecycleSubStep.DEPLOYING_ROLLING_BACK,
            )
        ]

    @classmethod
    @override
    def status_transitions(cls) -> DeploymentStatusTransitions:
        ready = DeploymentLifecycleStatus(
            lifecycle=EndpointLifecycle.READY,
            sub_step=None,
        )
        return DeploymentStatusTransitions(
            success=ready,
            need_retry=None,
            expired=ready,
            give_up=ready,
        )

    @override
    async def execute(
        self, deployments: Sequence[DeploymentWithHistory]
    ) -> DeploymentExecutionResult:
        all_deployment_ids = {deployment.deployment_info.id for deployment in deployments}
        await self._deployment_repo.clear_deploying_revision(all_deployment_ids)
        log.info(
            "Cleared deploying_revision for {} rolling-back deployments",
            len(all_deployment_ids),
        )

        return DeploymentExecutionResult(successes=list(deployments))

    @override
    async def post_process(self, result: DeploymentExecutionResult) -> None:
        await self._deployment_controller.mark_lifecycle_needed(
            DeploymentLifecycleType.DEPLOYING,
            sub_step=DeploymentLifecycleSubStep.DEPLOYING_ROLLING_BACK,
        )
        await self._route_controller.mark_lifecycle_needed(RouteLifecycleType.PROVISIONING)
