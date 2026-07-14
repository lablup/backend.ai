from __future__ import annotations

from collections.abc import Sequence
from typing import override

from ai.backend.common.identifier.replica_group import ReplicaGroupID
from ai.backend.common.schema.deployment import TrafficStepInput
from ai.backend.manager.data.deployment.types import (
    DeploymentHandlerCategory,
    DeploymentLifecycleStatus,
    DeploymentLifecycleSubStep,
    DeploymentStatusTransitions,
    DeploymentTargetStatuses,
)
from ai.backend.manager.data.model_serving.types import EndpointLifecycle
from ai.backend.manager.defs import LockID
from ai.backend.manager.models.replica_group import ReplicaGroupRow
from ai.backend.manager.models.replica_group.conditions import ReplicaGroupConditions
from ai.backend.manager.repositories.base import BatchQuerier, NoPagination
from ai.backend.manager.repositories.base.updater import Updater
from ai.backend.manager.repositories.deployment.updaters.replica_group import (
    ReplicaGroupDeployUpdaterSpec,
)
from ai.backend.manager.repositories.replica_group.repository import ReplicaGroupRepository
from ai.backend.manager.sokovan.deployment.deployment_controller import DeploymentController
from ai.backend.manager.sokovan.deployment.types import (
    DeploymentExecutionError,
    DeploymentExecutionResult,
    DeploymentLifecycleType,
    DeploymentWithHistory,
)
from ai.backend.manager.types import OptionalState
from ai.backend.manager.views.replica_group import ReplicaGroupDeploySchedulingView

from .base import DeploymentHandler


class DeployingPromotingHandler(DeploymentHandler):
    """DEPLOYING / PROMOTING: shift traffic to the STABLE target group per the strategy, one step
    per tick. Once the shift completes, hand off to FINALIZING (which swaps the target in as
    primary). Only traffic weights are written here."""

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
        return "deploying-promoting"

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
            sub_steps=[DeploymentLifecycleSubStep.DEPLOYING_PROMOTING],
        )

    @classmethod
    @override
    def status_transitions(cls) -> DeploymentStatusTransitions:
        return DeploymentStatusTransitions(
            success=DeploymentLifecycleStatus(
                lifecycle=EndpointLifecycle.DEPLOYING,
                sub_step=DeploymentLifecycleSubStep.DEPLOYING_FINALIZING,
            ),
            need_retry=DeploymentLifecycleStatus(
                lifecycle=EndpointLifecycle.DEPLOYING,
                sub_step=DeploymentLifecycleSubStep.DEPLOYING_PROMOTING,
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
        now = await self._replica_group_repository.current_time()
        deployment_ids = [d.deployment_info.id for d in deployments]
        querier = BatchQuerier(
            pagination=NoPagination(),
            conditions=[ReplicaGroupConditions.by_deployment_ids(deployment_ids)],
        )
        views = await self._replica_group_repository.search_deploy_scheduling_views(querier)
        groups_by_id: dict[ReplicaGroupID, ReplicaGroupDeploySchedulingView] = {
            view.group_id: view for view in views
        }

        completed: list[DeploymentWithHistory] = []
        failures: list[DeploymentExecutionError] = []
        group_updaters: list[Updater[ReplicaGroupRow]] = []

        for deployment in deployments:
            info = deployment.deployment_info
            target = (
                groups_by_id.get(info.target_replica_group_id)
                if info.target_replica_group_id is not None
                else None
            )
            if info.policy is None or target is None:
                failures.append(
                    DeploymentExecutionError(
                        deployment_info=deployment,
                        reason="Cannot promote target replica group",
                        error_detail="Deployment has no policy or target replica group to promote",
                    )
                )
                continue
            # Rolling reuses the primary as the target, so there is no separate serving group
            # (and we must not set both 100 and 0 on the same group).
            primary_group_id = info.primary_replica_group_id
            serving = (
                groups_by_id.get(primary_group_id)
                if primary_group_id is not None and primary_group_id != target.group_id
                else None
            )
            last_changed_at = (
                deployment.last_history.started_at if deployment.last_history is not None else now
            )
            step = info.policy.strategy_spec.traffic_step(
                TrafficStepInput(
                    target_traffic_weight=target.traffic_weight,
                    serving_traffic_weight=serving.traffic_weight if serving is not None else 0,
                    last_changed_at=last_changed_at,
                    now=now,
                )
            )
            group_updaters.append(
                Updater(
                    pk_value=target.group_id,
                    spec=ReplicaGroupDeployUpdaterSpec(
                        traffic_weight=OptionalState.update(step.target_traffic_weight),
                    ),
                )
            )
            if serving is not None:
                group_updaters.append(
                    Updater(
                        pk_value=serving.group_id,
                        spec=ReplicaGroupDeployUpdaterSpec(
                            traffic_weight=OptionalState.update(step.serving_traffic_weight),
                        ),
                    )
                )
            if step.completed:
                completed.append(deployment)
            else:
                failures.append(
                    DeploymentExecutionError(
                        deployment_info=deployment,
                        reason="Traffic shift in progress",
                        error_detail="Target replica group has not reached full traffic yet",
                    )
                )

        successes: list[DeploymentWithHistory] = []
        result = await self._replica_group_repository.apply_writes(
            group_updaters=group_updaters,
            endpoint_updaters=[],
        )
        for deployment in completed:
            if deployment.deployment_info.target_replica_group_id in result.updated_group_ids:
                successes.append(deployment)
            else:
                failures.append(
                    DeploymentExecutionError(
                        deployment_info=deployment,
                        reason="Failed to shift traffic weight",
                        error_detail="Target replica group weight update was not applied",
                    )
                )

        return DeploymentExecutionResult(successes=successes, failures=failures)

    @override
    async def post_process(self, result: DeploymentExecutionResult) -> None:
        if result.successes:
            await self._deployment_controller.mark_lifecycle_needed(
                DeploymentLifecycleType.DEPLOYING,
                sub_step=DeploymentLifecycleSubStep.DEPLOYING_FINALIZING,
            )
