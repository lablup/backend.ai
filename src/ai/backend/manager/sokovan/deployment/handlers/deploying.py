"""Handlers for DEPLOYING sub-steps (BEP-1049).

All sub-step handlers are registered flat in the coordinator alongside other
lifecycle handlers.  The coordinator dispatches by sub-step using the
``(lifecycle_type, sub_step)`` registry key.

Each handler's ``execute()`` evaluates the strategy FSM and classifies
deployments into successes / errors / skipped.  The coordinator then
applies ``status_transitions()`` to move deployments to the next sub-step
or lifecycle state.

Sub-step flow::

    PROVISIONING ──success──▸ PROGRESSING ──success──▸ READY
                                  │                   (via COMPLETED marker)
                                  │failure
                                  ▼
                             ROLLING_BACK ──success──▸ READY
                                                      (via ROLLED_BACK marker)
"""

from __future__ import annotations

import logging
from collections.abc import Sequence
from typing import override

from ai.backend.logging import BraceStyleAdapter
from ai.backend.manager.data.deployment.types import (
    DeploymentLifecycleStatus,
    DeploymentStatusTransitions,
    DeploymentSubStep,
)
from ai.backend.manager.data.model_serving.types import EndpointLifecycle
from ai.backend.manager.defs import LockID
from ai.backend.manager.sokovan.deployment.deployment_controller import DeploymentController
from ai.backend.manager.sokovan.deployment.route.route_controller import RouteController
from ai.backend.manager.sokovan.deployment.route.types import RouteLifecycleType
from ai.backend.manager.sokovan.deployment.types import (
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
    """Handler for DEPLOYING / PROVISIONING sub-step.

    New-revision routes are being created; waiting for them to become HEALTHY.

    - success: Routes provisioned → transition to PROGRESSING.
    - failure: Provisioning failed → transition to ROLLING_BACK.
    - skipped: Still waiting for routes — no transition, re-schedule.
    """

    def __init__(
        self,
        deployment_controller: DeploymentController,
        route_controller: RouteController,
    ) -> None:
        self._deployment_controller = deployment_controller
        self._route_controller = route_controller

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
                sub_status=DeploymentSubStep.PROVISIONING,
            )
        ]

    @classmethod
    @override
    def status_transitions(cls) -> DeploymentStatusTransitions:
        return DeploymentStatusTransitions(
            success=DeploymentLifecycleStatus(
                lifecycle=EndpointLifecycle.DEPLOYING,
                sub_status=DeploymentSubStep.PROGRESSING,
            ),
            need_retry=None,
            expired=DeploymentLifecycleStatus(
                lifecycle=EndpointLifecycle.DEPLOYING,
                sub_status=DeploymentSubStep.ROLLING_BACK,
            ),
            give_up=DeploymentLifecycleStatus(
                lifecycle=EndpointLifecycle.DEPLOYING,
                sub_status=DeploymentSubStep.ROLLING_BACK,
            ),
        )

    @override
    async def execute(
        self, deployments: Sequence[DeploymentWithHistory]
    ) -> DeploymentExecutionResult:
        raise NotImplementedError("Strategy evaluator and applier are not yet wired — see BA-5014")

    @override
    async def post_process(self, result: DeploymentExecutionResult) -> None:
        await self._deployment_controller.mark_lifecycle_needed(
            DeploymentLifecycleType.DEPLOYING, sub_step=DeploymentSubStep.PROVISIONING
        )
        await self._route_controller.mark_lifecycle_needed(RouteLifecycleType.PROVISIONING)


class DeployingProgressingHandler(DeploymentHandler):
    """Handler for DEPLOYING / PROGRESSING sub-step (+ COMPLETED marker).

    Targets PROGRESSING (active) and COMPLETED (terminal marker):

    - success: Strategy conditions met (COMPLETED) → transition to READY.
    - expired/give_up: Strategy failed → transition to ROLLING_BACK.
    - skipped: Still progressing — no transition, re-schedule.
    """

    def __init__(
        self,
        deployment_controller: DeploymentController,
        route_controller: RouteController,
    ) -> None:
        self._deployment_controller = deployment_controller
        self._route_controller = route_controller

    @classmethod
    @override
    def name(cls) -> str:
        return "deploying-progressing"

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
                sub_status=DeploymentSubStep.PROGRESSING,
            ),
            DeploymentLifecycleStatus(
                lifecycle=EndpointLifecycle.DEPLOYING,
                sub_status=DeploymentSubStep.COMPLETED,
            ),
        ]

    @classmethod
    @override
    def status_transitions(cls) -> DeploymentStatusTransitions:
        return DeploymentStatusTransitions(
            success=DeploymentLifecycleStatus(lifecycle=EndpointLifecycle.READY),
            need_retry=None,
            expired=DeploymentLifecycleStatus(
                lifecycle=EndpointLifecycle.DEPLOYING,
                sub_status=DeploymentSubStep.ROLLING_BACK,
            ),
            give_up=DeploymentLifecycleStatus(
                lifecycle=EndpointLifecycle.DEPLOYING,
                sub_status=DeploymentSubStep.ROLLING_BACK,
            ),
        )

    @override
    async def execute(
        self, deployments: Sequence[DeploymentWithHistory]
    ) -> DeploymentExecutionResult:
        raise NotImplementedError("Strategy evaluator and applier are not yet wired — see BA-5014")

    @override
    async def post_process(self, result: DeploymentExecutionResult) -> None:
        await self._deployment_controller.mark_lifecycle_needed(
            DeploymentLifecycleType.DEPLOYING, sub_step=DeploymentSubStep.PROGRESSING
        )
        await self._route_controller.mark_lifecycle_needed(RouteLifecycleType.PROVISIONING)


class DeployingRollingBackHandler(DeploymentHandler):
    """Handler for DEPLOYING / ROLLING_BACK sub-step.

    Actively rolling back — terminate new-revision routes,
    restore traffic to previous revision routes.

    - success: Rollback complete → transition to READY.
    - failure: Rollback itself failed → transition to READY (best-effort).
    - skipped: Still rolling back — no transition, re-schedule.
    """

    def __init__(
        self,
        deployment_controller: DeploymentController,
        route_controller: RouteController,
    ) -> None:
        self._deployment_controller = deployment_controller
        self._route_controller = route_controller

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
                sub_status=DeploymentSubStep.ROLLING_BACK,
            ),
        ]

    @classmethod
    @override
    def status_transitions(cls) -> DeploymentStatusTransitions:
        return DeploymentStatusTransitions(
            success=DeploymentLifecycleStatus(lifecycle=EndpointLifecycle.READY),
            need_retry=None,
            # TODO: How can we handle this?
            expired=DeploymentLifecycleStatus(lifecycle=EndpointLifecycle.READY),
            give_up=DeploymentLifecycleStatus(lifecycle=EndpointLifecycle.READY),
        )

    @override
    async def execute(
        self, deployments: Sequence[DeploymentWithHistory]
    ) -> DeploymentExecutionResult:
        raise NotImplementedError("Strategy evaluator and applier are not yet wired — see BA-5014")

    @override
    async def post_process(self, result: DeploymentExecutionResult) -> None:
        await self._deployment_controller.mark_lifecycle_needed(
            DeploymentLifecycleType.DEPLOYING, sub_step=DeploymentSubStep.ROLLING_BACK
        )
        await self._route_controller.mark_lifecycle_needed(RouteLifecycleType.PROVISIONING)
