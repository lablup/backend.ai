from __future__ import annotations

import logging
from collections.abc import Sequence
from typing import override

from ai.backend.common.identifier.replica_group import ReplicaGroupID
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


class DeployingProvisionedHandler(DeploymentHandler):
    """DEPLOYING / PROVISIONED: wait for the target replica group to reach STABLE (its replicas
    have come up), then hand off to PROMOTING. Read-only — the group scaling/rolling reconcile
    fills routes and steps counts; this handler only polls the group lifecycle."""

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
        return "deploying-provisioned"

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
            sub_steps=[DeploymentLifecycleSubStep.DEPLOYING_PROVISIONED],
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
                sub_step=DeploymentLifecycleSubStep.DEPLOYING_PROVISIONED,
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
        groups_by_id: dict[ReplicaGroupID, ReplicaGroupDeploySchedulingView] = {
            view.group_id: view for view in views
        }

        successes: list[DeploymentWithHistory] = []
        failures: list[DeploymentExecutionError] = []

        for deployment in deployments:
            info = deployment.deployment_info
            target = (
                groups_by_id.get(info.target_replica_group_id)
                if info.target_replica_group_id is not None
                else None
            )
            if target is None:
                failures.append(
                    DeploymentExecutionError(
                        deployment_info=deployment,
                        reason="Target replica group missing",
                        error_detail="Deployment reached PROVISIONED without a target replica group",
                    )
                )
            elif target.lifecycle in (
                ReplicaGroupLifecycle.FAILED,
                ReplicaGroupLifecycle.DRAINING,
                ReplicaGroupLifecycle.DRAINED,
            ):
                failures.append(
                    DeploymentExecutionError(
                        deployment_info=deployment,
                        reason="Target replica group cannot roll out",
                        error_detail=(
                            f"Target replica group entered {target.lifecycle.value} "
                            "while provisioning"
                        ),
                    )
                )
            elif target.lifecycle is ReplicaGroupLifecycle.STABLE:
                successes.append(deployment)
            else:
                failures.append(
                    DeploymentExecutionError(
                        deployment_info=deployment,
                        reason="Target replica group not yet stable",
                        error_detail=(
                            f"Target replica group still {target.lifecycle.value}; "
                            "waiting for replicas to come up"
                        ),
                    )
                )

        return DeploymentExecutionResult(successes=successes, failures=failures, skipped=[])

    @override
    async def post_process(self, result: DeploymentExecutionResult) -> None:
        if result.successes:
            await self._deployment_controller.mark_lifecycle_needed(
                DeploymentLifecycleType.DEPLOYING,
                sub_step=DeploymentLifecycleSubStep.DEPLOYING_PROMOTING,
            )
