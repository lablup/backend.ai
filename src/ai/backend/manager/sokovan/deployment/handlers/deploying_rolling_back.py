from __future__ import annotations

import logging
from collections.abc import Sequence
from typing import override

from ai.backend.logging import BraceStyleAdapter
from ai.backend.manager.data.deployment.types import (
    DeploymentHandlerCategory,
    DeploymentLifecycleStatus,
    DeploymentLifecycleSubStep,
    DeploymentStatusTransitions,
    DeploymentTargetStatuses,
)
from ai.backend.manager.data.model_serving.types import EndpointLifecycle
from ai.backend.manager.defs import LockID
from ai.backend.manager.repositories.deployment.repository import DeploymentRepository
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


class DeployingRollingBackHandler(DeploymentHandler):
    """Handler for DEPLOYING / ROLLING_BACK sub-step."""

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
            sub_steps=[DeploymentLifecycleSubStep.DEPLOYING_ROLLING_BACK],
        )

    @classmethod
    @override
    def status_transitions(cls) -> DeploymentStatusTransitions:
        return DeploymentStatusTransitions(
            success=DeploymentLifecycleStatus(
                lifecycle=EndpointLifecycle.READY,
                sub_step=None,
            ),
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
