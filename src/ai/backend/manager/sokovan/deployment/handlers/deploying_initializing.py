from __future__ import annotations

from collections.abc import Sequence
from typing import override

from ai.backend.common.identifier.deployment_revision import DeploymentRevisionID
from ai.backend.manager.data.deployment.types import (
    DeploymentHandlerCategory,
    DeploymentLifecycleStatus,
    DeploymentLifecycleSubStep,
    DeploymentStatusTransitions,
    DeploymentTargetStatuses,
)
from ai.backend.manager.data.model_serving.types import EndpointLifecycle
from ai.backend.manager.defs import LockID
from ai.backend.manager.sokovan.deployment.deployment_controller import DeploymentController
from ai.backend.manager.sokovan.deployment.executor import DeploymentExecutor
from ai.backend.manager.sokovan.deployment.types import (
    DeploymentExecutionResult,
    DeploymentLifecycleType,
    DeploymentWithHistory,
)

from .base import DeploymentHandler


class DeployingInitializingHandler(DeploymentHandler):
    """DEPLOYING / INITIALIZING: register the appproxy endpoint for deployments that entered
    DEPLOYING via ActivateRevision (and so skipped check_pending), then hand off to
    PROVISIONING which sets up the target replica group."""

    def __init__(
        self,
        deployment_controller: DeploymentController,
        deployment_executor: DeploymentExecutor,
    ) -> None:
        self._deployment_controller = deployment_controller
        self._deployment_executor = deployment_executor

    @classmethod
    @override
    def name(cls) -> str:
        return "deploying-initializing"

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
            sub_steps=[DeploymentLifecycleSubStep.DEPLOYING_INITIALIZING],
        )

    @classmethod
    @override
    def status_transitions(cls) -> DeploymentStatusTransitions:
        return DeploymentStatusTransitions(
            success=DeploymentLifecycleStatus(
                lifecycle=EndpointLifecycle.DEPLOYING,
                sub_step=DeploymentLifecycleSubStep.DEPLOYING_PROVISIONING,
            ),
            need_retry=DeploymentLifecycleStatus(
                lifecycle=EndpointLifecycle.DEPLOYING,
                sub_step=DeploymentLifecycleSubStep.DEPLOYING_INITIALIZING,
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

    @override
    async def execute(
        self, deployments: Sequence[DeploymentWithHistory]
    ) -> DeploymentExecutionResult:
        ready: list[DeploymentWithHistory] = []
        entries: list[tuple[DeploymentWithHistory, DeploymentRevisionID]] = []
        for deployment in deployments:
            info = deployment.deployment_info
            if info.network.url is not None or info.deploying_revision is None:
                ready.append(deployment)
            else:
                entries.append((deployment, info.deploying_revision.id))

        successes = list(ready)
        skipped: list[DeploymentWithHistory] = []
        if entries:
            result = await self._deployment_executor.register_endpoints_bulk(entries)
            failed_ids = {error.deployment_info.deployment_info.id for error in result.failures}
            for deployment, _ in entries:
                if deployment.deployment_info.id in failed_ids:
                    skipped.append(deployment)
                else:
                    successes.append(deployment)

        return DeploymentExecutionResult(successes=successes, skipped=skipped)

    @override
    async def post_process(self, result: DeploymentExecutionResult) -> None:
        if result.successes:
            await self._deployment_controller.mark_lifecycle_needed(
                DeploymentLifecycleType.DEPLOYING,
                sub_step=DeploymentLifecycleSubStep.DEPLOYING_PROVISIONING,
            )
