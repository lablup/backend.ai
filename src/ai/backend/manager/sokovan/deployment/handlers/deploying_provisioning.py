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
from ai.backend.manager.repositories.replica_group.repository import ReplicaGroupRepository
from ai.backend.manager.repositories.replica_group.types import GroupRolloutSetup
from ai.backend.manager.sokovan.deployment.deployment_controller import DeploymentController
from ai.backend.manager.sokovan.deployment.types import (
    DeploymentExecutionError,
    DeploymentExecutionResult,
    DeploymentLifecycleType,
    DeploymentWithHistory,
)

from .base import DeploymentHandler

log = BraceStyleAdapter(logging.getLogger(__name__))


class DeployingProvisioningHandler(DeploymentHandler):
    """DEPLOYING / PROVISIONING: set up the target replica group for the deploying revision
    (rolling reuses the primary group, blue-green/canary creates a new one), then hand off to
    PROVISIONED which waits for it to reach STABLE."""

    def __init__(
        self,
        deployment_controller: DeploymentController,
        replica_group_repository: ReplicaGroupRepository,
    ) -> None:
        self._deployment_controller = deployment_controller
        self._replica_group_repository = replica_group_repository

    @classmethod
    @override
    def name(cls) -> str:
        return "deploying-provisioning"

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
            sub_steps=[DeploymentLifecycleSubStep.DEPLOYING_PROVISIONING],
        )

    @classmethod
    @override
    def status_transitions(cls) -> DeploymentStatusTransitions:
        return DeploymentStatusTransitions(
            success=DeploymentLifecycleStatus(
                lifecycle=EndpointLifecycle.DEPLOYING,
                sub_step=DeploymentLifecycleSubStep.DEPLOYING_PROVISIONED,
            ),
            need_retry=DeploymentLifecycleStatus(
                lifecycle=EndpointLifecycle.DEPLOYING,
                sub_step=DeploymentLifecycleSubStep.DEPLOYING_PROVISIONING,
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
        failures: list[DeploymentExecutionError] = []
        setups: list[GroupRolloutSetup] = []
        to_set_up: list[DeploymentWithHistory] = []

        for deployment in deployments:
            info = deployment.deployment_info
            if info.policy is None or info.deploying_revision_id is None:
                failures.append(
                    DeploymentExecutionError(
                        deployment_info=deployment,
                        reason="Cannot set up target replica group",
                        error_detail="Deployment has no policy or deploying revision to provision",
                    )
                )
                continue
            setups.append(
                GroupRolloutSetup(
                    deployment_id=info.id,
                    target_revision_id=info.deploying_revision_id,
                    spec=info.policy.strategy_spec.rollout_target(),
                    desired_target_replica_count=info.replica.target_replica_count,
                )
            )
            to_set_up.append(deployment)

        successes: list[DeploymentWithHistory] = []
        if setups:
            done_ids = await self._replica_group_repository.setup_target_groups(setups)
            for deployment in to_set_up:
                if deployment.deployment_info.id in done_ids:
                    successes.append(deployment)
                else:
                    failures.append(
                        DeploymentExecutionError(
                            deployment_info=deployment,
                            reason="Failed to set up target replica group",
                            error_detail="Endpoint target replica group pointer was not set",
                        )
                    )

        return DeploymentExecutionResult(successes=successes, failures=failures)

    @override
    async def post_process(self, result: DeploymentExecutionResult) -> None:
        if result.successes:
            await self._deployment_controller.mark_lifecycle_needed(
                DeploymentLifecycleType.DEPLOYING,
                sub_step=DeploymentLifecycleSubStep.DEPLOYING_PROVISIONED,
            )
