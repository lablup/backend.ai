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
from ai.backend.manager.models.endpoint import EndpointRow
from ai.backend.manager.models.replica_group import ReplicaGroupRow
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
    DeploymentExecutionError,
    DeploymentExecutionResult,
    DeploymentLifecycleType,
    DeploymentWithHistory,
)
from ai.backend.manager.types import OptionalState, TriState

from .base import DeploymentHandler


class DeployingFinalizingHandler(DeploymentHandler):
    """DEPLOYING / FINALIZING: the traffic shift is complete, so make the target group the sole
    serving group — set it to full traffic weight, drop the superseded primary to zero, point the
    endpoint's primary_replica_group_id at the target and clear target_replica_group_id — then hand
    off to DRAINING. The group's own current/target revision swap is done by the group lifecycle
    reconcile when it reaches STABLE."""

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
        return "deploying-finalizing"

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
            sub_steps=[DeploymentLifecycleSubStep.DEPLOYING_FINALIZING],
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
                sub_step=DeploymentLifecycleSubStep.DEPLOYING_FINALIZING,
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
        successes: list[DeploymentWithHistory] = []
        failures: list[DeploymentExecutionError] = []
        group_updaters: list[Updater[ReplicaGroupRow]] = []
        endpoint_updaters: list[Updater[EndpointRow]] = []
        to_finalize: list[DeploymentWithHistory] = []

        for deployment in deployments:
            info = deployment.deployment_info
            target_group_id = info.target_replica_group_id
            if target_group_id is None:
                failures.append(
                    DeploymentExecutionError(
                        deployment_info=deployment,
                        reason="No target replica group to finalize",
                        error_detail="Deployment reached FINALIZING without a target replica group",
                    )
                )
                continue
            # The target now serves all traffic; drop the superseded primary to none. Rolling
            # reuses the primary as target, so there is nothing to demote.
            group_updaters.append(
                Updater(
                    pk_value=target_group_id,
                    spec=ReplicaGroupDeployUpdaterSpec(traffic_weight=OptionalState.update(100)),
                )
            )
            primary_group_id = info.primary_replica_group_id
            if primary_group_id is not None and primary_group_id != target_group_id:
                group_updaters.append(
                    Updater(
                        pk_value=primary_group_id,
                        spec=ReplicaGroupDeployUpdaterSpec(traffic_weight=OptionalState.update(0)),
                    )
                )
            endpoint_updaters.append(
                Updater(
                    pk_value=info.id,
                    spec=EndpointReplicaGroupUpdaterSpec(
                        primary_replica_group_id=OptionalState.update(target_group_id),
                        target_replica_group_id=TriState.nullify(),
                    ),
                )
            )
            to_finalize.append(deployment)

        result = await self._replica_group_repository.apply_writes(
            group_updaters=group_updaters,
            endpoint_updaters=endpoint_updaters,
        )
        for deployment in to_finalize:
            if deployment.deployment_info.id in result.updated_endpoint_ids:
                successes.append(deployment)
            else:
                failures.append(
                    DeploymentExecutionError(
                        deployment_info=deployment,
                        reason="Failed to finalize deployment",
                        error_detail="Endpoint primary replica group swap was not applied",
                    )
                )

        return DeploymentExecutionResult(successes=successes, failures=failures)

    @override
    async def post_process(self, result: DeploymentExecutionResult) -> None:
        if result.successes:
            await self._deployment_controller.mark_lifecycle_needed(
                DeploymentLifecycleType.DEPLOYING,
                sub_step=DeploymentLifecycleSubStep.DEPLOYING_DRAINING,
            )
