from __future__ import annotations

import logging
from collections.abc import Sequence
from typing import override

from ai.backend.common.identifier.deployment import DeploymentID
from ai.backend.logging import BraceStyleAdapter
from ai.backend.manager.data.deployment.types import (
    DeploymentHandlerCategory,
    DeploymentLifecycleStatus,
    DeploymentLifecycleSubStep,
    DeploymentStatusTransitions,
    DeploymentTargetStatuses,
    ReplicaGroupLifecycle,
)
from ai.backend.manager.data.model_serving.types import EndpointLifecycle
from ai.backend.manager.defs import LockID
from ai.backend.manager.models.replica_group.conditions import ReplicaGroupConditions
from ai.backend.manager.repositories.base import BatchQuerier, NoPagination
from ai.backend.manager.repositories.replica_group.repository import ReplicaGroupRepository
from ai.backend.manager.sokovan.deployment.deployment_controller import DeploymentController
from ai.backend.manager.sokovan.deployment.types import (
    DeploymentExecutionError,
    DeploymentExecutionResult,
    DeploymentLifecycleType,
    DeploymentWithHistory,
)
from ai.backend.manager.views.replica_group import ReplicaGroupDeploySchedulingView

from .base import DeploymentHandler

log = BraceStyleAdapter(logging.getLogger(__name__))


class DeployingProvisioningHandler(DeploymentHandler):
    """DEPLOYING / PROVISIONING: wait for the target replica group (the one rolling out the
    deploying revision) to reach STABLE, then hand off to PROMOTING. The group scaling/rolling
    reconcile fills routes and steps counts; this handler only polls the group lifecycle."""

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
                sub_step=DeploymentLifecycleSubStep.DEPLOYING_PROMOTING,
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
        deployment_ids = [d.deployment_info.id for d in deployments]
        querier = BatchQuerier(
            pagination=NoPagination(),
            conditions=[ReplicaGroupConditions.by_deployment_ids(deployment_ids)],
        )
        views = await self._replica_group_repository.search_deploy_scheduling_views(querier)
        groups_by_deployment: dict[DeploymentID, list[ReplicaGroupDeploySchedulingView]] = {}
        for view in views:
            groups_by_deployment.setdefault(view.deployment_id, []).append(view)

        successes: list[DeploymentWithHistory] = []
        failures: list[DeploymentExecutionError] = []
        skipped: list[DeploymentWithHistory] = []

        for deployment in deployments:
            info = deployment.deployment_info
            if info.target_replica_group_id is None:
                skipped.append(deployment)
                continue
            target = next(
                (
                    group
                    for group in groups_by_deployment.get(info.id, [])
                    if group.group_id == info.target_replica_group_id
                ),
                None,
            )
            if target is None:
                skipped.append(deployment)
            elif target.lifecycle is ReplicaGroupLifecycle.FAILED:
                failures.append(
                    DeploymentExecutionError(
                        deployment_info=deployment,
                        reason="Target replica group failed to roll out",
                        error_detail="The target replica group entered FAILED during provisioning",
                    )
                )
            elif target.lifecycle is ReplicaGroupLifecycle.STABLE:
                successes.append(deployment)
            else:
                skipped.append(deployment)

        return DeploymentExecutionResult(successes=successes, failures=failures, skipped=skipped)

    @override
    async def post_process(self, result: DeploymentExecutionResult) -> None:
        if result.successes:
            await self._deployment_controller.mark_lifecycle_needed(
                DeploymentLifecycleType.DEPLOYING,
                sub_step=DeploymentLifecycleSubStep.DEPLOYING_PROMOTING,
            )
        if result.failures:
            await self._deployment_controller.mark_lifecycle_needed(
                DeploymentLifecycleType.DEPLOYING,
                sub_step=DeploymentLifecycleSubStep.DEPLOYING_ROLLING_BACK,
            )
