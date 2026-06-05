from __future__ import annotations

from collections.abc import Sequence
from typing import override

from ai.backend.manager.data.deployment.types import (
    DeploymentHandlerCategory,
    DeploymentLifecycleStatus,
    DeploymentLifecycleSubStep,
    DeploymentStatusTransitions,
    DeploymentTargetStatuses,
)
from ai.backend.manager.data.model_serving.types import EndpointLifecycle
from ai.backend.manager.defs import LockID
from ai.backend.manager.sokovan.deployment.types import (
    DeploymentExecutionResult,
    DeploymentWithHistory,
)

from .base import DeploymentHandler


class DeployingDrainingHandler(DeploymentHandler):
    """DEPLOYING / DRAINING: wait for the superseded group(s) to fully drain (DRAINED), then
    clear deploying_revision and finish (READY). Rolling drains in place, so nothing to wait."""

    @classmethod
    @override
    def name(cls) -> str:
        return "deploying-draining"

    @classmethod
    @override
    def category(cls) -> DeploymentHandlerCategory:
        return DeploymentHandlerCategory.LIFECYCLE

    @property
    @override
    def lock_id(self) -> LockID | None:
        return LockID.LOCKID_DEPLOYMENT_DEPLOYING

    @classmethod
    @override
    def target_statuses(cls) -> DeploymentTargetStatuses:
        return DeploymentTargetStatuses(
            lifecycle_stages=[EndpointLifecycle.DEPLOYING],
            sub_steps=[DeploymentLifecycleSubStep.DEPLOYING_DRAINING],
        )

    @classmethod
    @override
    def status_transitions(cls) -> DeploymentStatusTransitions:
        ready = DeploymentLifecycleStatus(
            lifecycle=EndpointLifecycle.READY,
            sub_step=None,
        )
        return DeploymentStatusTransitions(
            success=ready,
            need_retry=DeploymentLifecycleStatus(
                lifecycle=EndpointLifecycle.DEPLOYING,
                sub_step=DeploymentLifecycleSubStep.DEPLOYING_DRAINING,
            ),
            expired=ready,
            give_up=ready,
        )

    @override
    async def execute(
        self, deployments: Sequence[DeploymentWithHistory]
    ) -> DeploymentExecutionResult:
        raise NotImplementedError

    @override
    async def post_process(self, result: DeploymentExecutionResult) -> None:
        raise NotImplementedError
