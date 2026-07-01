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
    ReplicaGroupLifecycle,
    ReplicaGroupScalingStatus,
)
from ai.backend.manager.data.model_serving.types import EndpointLifecycle
from ai.backend.manager.defs import LockID
from ai.backend.manager.models.endpoint import EndpointRow
from ai.backend.manager.models.replica_group import ReplicaGroupRow
from ai.backend.manager.repositories.base.updater import Updater
from ai.backend.manager.repositories.deployment.repository import DeploymentRepository
from ai.backend.manager.repositories.deployment.updaters.deployment import (
    EndpointReplicaGroupUpdaterSpec,
)
from ai.backend.manager.repositories.deployment.updaters.replica_group import (
    ReplicaGroupDeployUpdaterSpec,
    ReplicaGroupLifecycleUpdaterSpec,
)
from ai.backend.manager.repositories.replica_group.repository import ReplicaGroupRepository
from ai.backend.manager.sokovan.deployment.route.route_controller import RouteController
from ai.backend.manager.sokovan.deployment.route.types import RouteLifecycleType
from ai.backend.manager.sokovan.deployment.types import (
    DeploymentExecutionError,
    DeploymentExecutionResult,
    DeploymentWithHistory,
)
from ai.backend.manager.types import OptionalState, TriState

from .base import DeploymentHandler

log = BraceStyleAdapter(logging.getLogger(__name__))


class DeployingRollingBackHandler(DeploymentHandler):
    """DEPLOYING / ROLLING_BACK: abandon the failed rollout and restore the current revision.

    Roll back the group changes — rolling drops the in-place target revision and refills the
    current revision to the goal; blue-green/canary drains the failed target group — then clear the
    endpoint's target pointer and the deploying revision and go READY. A deployment with no current
    revision (a failed initial deploy) has nothing to roll back to and goes to DESTROYING."""

    def __init__(
        self,
        route_controller: RouteController,
        deployment_repo: DeploymentRepository,
        replica_group_repository: ReplicaGroupRepository,
    ) -> None:
        self._route_controller = route_controller
        self._deployment_repo = deployment_repo
        self._replica_group_repository = replica_group_repository

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
        destroying = DeploymentLifecycleStatus(
            lifecycle=EndpointLifecycle.DESTROYING,
            sub_step=None,
        )
        return DeploymentStatusTransitions(
            success=DeploymentLifecycleStatus(
                lifecycle=EndpointLifecycle.READY,
                sub_step=None,
            ),
            need_retry=destroying,
            expired=destroying,
            give_up=destroying,
        )

    @override
    async def execute(
        self, deployments: Sequence[DeploymentWithHistory]
    ) -> DeploymentExecutionResult:
        rollback_targets: list[DeploymentWithHistory] = []
        failures: list[DeploymentExecutionError] = []
        group_updaters: list[Updater[ReplicaGroupRow]] = []
        endpoint_updaters: list[Updater[EndpointRow]] = []

        for deployment in deployments:
            info = deployment.deployment_info
            if info.current_revision is None:
                failures.append(
                    DeploymentExecutionError(
                        deployment_info=deployment,
                        reason="No current revision to roll back to",
                        error_detail=(
                            "Initial deployment failed; current_revision is None. "
                            "Transitioning to DESTROYING."
                        ),
                    )
                )
                continue
            target_group_id = info.target_replica_group_id
            if target_group_id is not None:
                if target_group_id == info.primary_replica_group_id:
                    # Rolling: drop the in-place target and refill the current revision to the goal.
                    group_updaters.append(
                        Updater(
                            pk_value=target_group_id,
                            spec=ReplicaGroupLifecycleUpdaterSpec(
                                lifecycle=OptionalState.update(ReplicaGroupLifecycle.STABLE),
                                desired_current_replica_count=OptionalState.update(
                                    info.replica.target_replica_count
                                ),
                                desired_target_replica_count=OptionalState.update(0),
                                scaling_status=OptionalState.update(
                                    ReplicaGroupScalingStatus.SCALING
                                ),
                                target_revision_id=TriState.nullify(),
                            ),
                        )
                    )
                else:
                    # Blue-green/canary: drain the failed target group (emptied by the reconcile).
                    group_updaters.append(
                        Updater(
                            pk_value=target_group_id,
                            spec=ReplicaGroupDeployUpdaterSpec(
                                lifecycle=OptionalState.update(ReplicaGroupLifecycle.DRAINING),
                            ),
                        )
                    )
                endpoint_updaters.append(
                    Updater(
                        pk_value=info.id,
                        spec=EndpointReplicaGroupUpdaterSpec(
                            target_replica_group_id=TriState.nullify(),
                        ),
                    )
                )
            rollback_targets.append(deployment)

        if group_updaters or endpoint_updaters:
            await self._replica_group_repository.apply_writes(
                group_updaters=group_updaters,
                endpoint_updaters=endpoint_updaters,
            )
        if rollback_targets:
            await self._deployment_repo.clear_deploying_revision({
                d.deployment_info.id for d in rollback_targets
            })

        return DeploymentExecutionResult(successes=rollback_targets, failures=failures)

    @override
    async def post_process(self, result: DeploymentExecutionResult) -> None:
        if result.successes:
            await self._route_controller.mark_lifecycle_needed(RouteLifecycleType.PROVISIONING)
