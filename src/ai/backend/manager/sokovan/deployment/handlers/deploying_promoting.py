from __future__ import annotations

from collections.abc import Sequence
from typing import override

from ai.backend.common.identifier.deployment import DeploymentID
from ai.backend.manager.data.deployment.types import (
    DeploymentHandlerCategory,
    DeploymentLifecycleStatus,
    DeploymentLifecycleSubStep,
    DeploymentStatusTransitions,
    DeploymentTargetStatuses,
    TrafficStepInput,
)
from ai.backend.manager.data.model_serving.types import EndpointLifecycle
from ai.backend.manager.defs import LockID
from ai.backend.manager.models.endpoint import EndpointRow
from ai.backend.manager.models.replica_group import ReplicaGroupRow
from ai.backend.manager.models.replica_group.conditions import ReplicaGroupConditions
from ai.backend.manager.repositories.base import BatchQuerier, NoPagination
from ai.backend.manager.repositories.base.updater import Updater
from ai.backend.manager.repositories.deployment.updaters.deployment import (
    EndpointReplicaGroupUpdaterSpec,
)
from ai.backend.manager.repositories.deployment.updaters.replica_group import (
    ReplicaGroupDeployUpdaterSpec,
)
from ai.backend.manager.repositories.replica_group.repository import ReplicaGroupRepository
from ai.backend.manager.sokovan.deployment.deployment_controller import DeploymentController
from ai.backend.manager.sokovan.deployment.types import (
    DeploymentExecutionResult,
    DeploymentLifecycleType,
    DeploymentWithHistory,
)
from ai.backend.manager.types import OptionalState, TriState
from ai.backend.manager.views.replica_group import ReplicaGroupDeploySchedulingView

from .base import DeploymentHandler


class DeployingPromotingHandler(DeploymentHandler):
    """DEPLOYING / PROMOTING: shift traffic to the (STABLE) target group per the strategy; once
    the shift completes, make it the serving group (current pointer + primary swap), then hand off
    to DRAINING (which retires the superseded group). All writes apply atomically."""

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
                sub_step=DeploymentLifecycleSubStep.DEPLOYING_DRAINING,
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
        groups_by_deployment: dict[DeploymentID, list[ReplicaGroupDeploySchedulingView]] = {}
        for view in views:
            groups_by_deployment.setdefault(view.deployment_id, []).append(view)

        successes: list[DeploymentWithHistory] = []
        skipped: list[DeploymentWithHistory] = []
        group_updaters: list[Updater[ReplicaGroupRow]] = []
        endpoint_updaters: list[Updater[EndpointRow]] = []

        for deployment in deployments:
            info = deployment.deployment_info
            deploying = info.deploying_revision_id
            target_group_id = info.target_replica_group_id
            if info.policy is None or deploying is None or target_group_id is None:
                skipped.append(deployment)
                continue
            groups = groups_by_deployment.get(info.id, [])
            target = next((g for g in groups if g.group_id == target_group_id), None)
            if target is None:
                skipped.append(deployment)
                continue
            superseded = [g for g in groups if g.group_id != target_group_id]
            serving_weight = superseded[0].traffic_weight if superseded else 0
            last_changed_at = (
                deployment.last_history.started_at if deployment.last_history is not None else now
            )
            step = info.policy.strategy_spec.traffic_step(
                TrafficStepInput(
                    target_traffic_weight=target.traffic_weight,
                    serving_traffic_weight=serving_weight,
                    last_changed_at=last_changed_at,
                    now=now,
                )
            )

            if step.completed:
                group_updaters.append(
                    Updater(
                        pk_value=target.group_id,
                        spec=ReplicaGroupDeployUpdaterSpec(
                            traffic_weight=OptionalState.update(step.target_traffic_weight),
                            current_revision_id=TriState.update(deploying),
                            target_revision_id=TriState.nullify(),
                        ),
                    )
                )
            else:
                group_updaters.append(
                    Updater(
                        pk_value=target.group_id,
                        spec=ReplicaGroupDeployUpdaterSpec(
                            traffic_weight=OptionalState.update(step.target_traffic_weight),
                        ),
                    )
                )
            for group in superseded:
                group_updaters.append(
                    Updater(
                        pk_value=group.group_id,
                        spec=ReplicaGroupDeployUpdaterSpec(
                            traffic_weight=OptionalState.update(step.serving_traffic_weight),
                        ),
                    )
                )

            if step.completed:
                endpoint_updaters.append(
                    Updater(
                        pk_value=info.id,
                        spec=EndpointReplicaGroupUpdaterSpec(
                            primary_replica_group_id=OptionalState.update(target_group_id),
                            target_replica_group_id=TriState.nullify(),
                        ),
                    )
                )
                successes.append(deployment)
            else:
                skipped.append(deployment)

        if group_updaters or endpoint_updaters:
            await self._replica_group_repository.apply_writes(
                group_updaters=group_updaters,
                endpoint_updaters=endpoint_updaters,
            )

        return DeploymentExecutionResult(successes=successes, skipped=skipped)

    @override
    async def post_process(self, result: DeploymentExecutionResult) -> None:
        if result.successes:
            await self._deployment_controller.mark_lifecycle_needed(
                DeploymentLifecycleType.DEPLOYING,
                sub_step=DeploymentLifecycleSubStep.DEPLOYING_DRAINING,
            )
