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
    ReplicaGroupLifecycle,
)
from ai.backend.manager.data.model_serving.types import EndpointLifecycle
from ai.backend.manager.defs import LockID
from ai.backend.manager.models.replica_group import ReplicaGroupRow
from ai.backend.manager.models.replica_group.conditions import ReplicaGroupConditions
from ai.backend.manager.repositories.base import BatchQuerier, NoPagination
from ai.backend.manager.repositories.base.updater import Updater
from ai.backend.manager.repositories.deployment.repository import DeploymentRepository
from ai.backend.manager.repositories.deployment.updaters.replica_group import (
    ReplicaGroupDeployUpdaterSpec,
)
from ai.backend.manager.repositories.replica_group.repository import ReplicaGroupRepository
from ai.backend.manager.sokovan.deployment.types import (
    DeploymentExecutionResult,
    DeploymentWithHistory,
)
from ai.backend.manager.types import OptionalState
from ai.backend.manager.views.replica_group import ReplicaGroupDeploySchedulingView

from .base import DeploymentHandler


class DeployingDrainingHandler(DeploymentHandler):
    """DEPLOYING / DRAINING: mark the superseded (non-primary) group(s) DRAINING and wait for the
    group draining reconcile to empty them (DRAINED), then clear deploying_revision and finish
    (READY). Rolling has no superseded group, so it finishes at once."""

    def __init__(
        self,
        replica_group_repository: ReplicaGroupRepository,
        deployment_repository: DeploymentRepository,
    ) -> None:
        self._replica_group_repository = replica_group_repository
        self._deployment_repository = deployment_repository

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
        drained_deployment_ids: set[DeploymentID] = set()
        for deployment in deployments:
            info = deployment.deployment_info
            superseded = [
                group
                for group in groups_by_deployment.get(info.id, [])
                if group.group_id != info.primary_replica_group_id
            ]
            # Start draining any superseded group still serving; the group draining reconcile
            # empties it to DRAINED.
            for group in superseded:
                if group.lifecycle is ReplicaGroupLifecycle.STABLE:
                    group_updaters.append(
                        Updater(
                            pk_value=group.group_id,
                            spec=ReplicaGroupDeployUpdaterSpec(
                                lifecycle=OptionalState.update(ReplicaGroupLifecycle.DRAINING),
                            ),
                        )
                    )
            pending = [
                group
                for group in superseded
                if group.lifecycle is not ReplicaGroupLifecycle.DRAINED
            ]
            if pending:
                skipped.append(deployment)
            else:
                successes.append(deployment)
                drained_deployment_ids.add(info.id)

        if group_updaters:
            await self._replica_group_repository.apply_writes(
                group_updaters=group_updaters,
                endpoint_updaters=[],
            )
        if drained_deployment_ids:
            await self._deployment_repository.clear_deploying_revision(drained_deployment_ids)

        return DeploymentExecutionResult(successes=successes, skipped=skipped)

    @override
    async def post_process(self, result: DeploymentExecutionResult) -> None:
        pass
