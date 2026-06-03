"""Database source for replica group repository operations."""

from __future__ import annotations

import logging
from collections.abc import Mapping, Sequence
from typing import TYPE_CHECKING
from uuid import UUID

import sqlalchemy as sa

from ai.backend.common.config import ModelHealthCheck
from ai.backend.common.data.permission.types import RBACElementType
from ai.backend.common.identifier.deployment import DeploymentID
from ai.backend.common.identifier.deployment_revision import DeploymentRevisionID
from ai.backend.common.identifier.replica_group import ReplicaGroupID
from ai.backend.logging.utils import BraceStyleAdapter
from ai.backend.manager.data.deployment.types import (
    ReplicaGroupHandlerCategory,
    RouteStatus,
    RouteTrafficStatus,
)
from ai.backend.manager.data.permission.types import RBACElementRef
from ai.backend.manager.data.reconciler.types import LastHistory
from ai.backend.manager.models.deployment_revision import DeploymentRevisionRow
from ai.backend.manager.models.endpoint import EndpointRow
from ai.backend.manager.models.replica_group import ReplicaGroupRow
from ai.backend.manager.models.replica_group_history import ReplicaGroupHistoryRow
from ai.backend.manager.models.replica_group_history.conditions import (
    ReplicaGroupHistoryConditions,
)
from ai.backend.manager.models.routing import RoutingRow
from ai.backend.manager.models.routing.conditions import RouteConditions
from ai.backend.manager.models.utils import ExtendedAsyncSAEngine
from ai.backend.manager.repositories.base import BatchQuerier, Creator, execute_batch_querier
from ai.backend.manager.repositories.base.rbac.entity_creator import RBACEntityCreator
from ai.backend.manager.repositories.base.updater import BatchUpdater, BulkUpdaterResult, Updater
from ai.backend.manager.repositories.deployment.creators import (
    RouteBatchUpdaterSpec,
    RouteCreatorSpec,
)
from ai.backend.manager.repositories.ops.sokovan.provider import SokovanOpsProvider, Transition
from ai.backend.manager.repositories.replica_group.types import (
    GroupRouteCreateInstruction,
    GroupRouteDrainInstruction,
    ReplicaGroupReconcileTransition,
    ReplicaGroupScalingReconcileApply,
    RevisionReplicaCount,
    ScalingReconcileFetch,
)
from ai.backend.manager.types import OptionalState
from ai.backend.manager.views.replica_group import (
    ReplicaGroupDeploySchedulingView,
    ReplicaGroupScalingReconcileView,
    ReplicaGroupScalingSchedulingView,
)

if TYPE_CHECKING:
    from sqlalchemy.ext.asyncio import AsyncSession as SASession

log = BraceStyleAdapter(logging.getLogger(__spec__.name))


class ReplicaGroupDBSource:
    _db: ExtendedAsyncSAEngine
    _ops: SokovanOpsProvider

    def __init__(self, db: ExtendedAsyncSAEngine) -> None:
        self._db = db
        self._ops = SokovanOpsProvider(db)

    async def search_deploy_scheduling_views(
        self,
        querier: BatchQuerier,
    ) -> list[ReplicaGroupDeploySchedulingView]:
        async with self._ops.read_ops() as r:
            result = await r.batch_query_in_global(sa.select(ReplicaGroupRow), querier)
            return [row.ReplicaGroupRow.to_deploy_scheduling_view() for row in result.rows]

    async def search_scaling_scheduling_views(
        self,
        querier: BatchQuerier,
    ) -> list[ReplicaGroupScalingSchedulingView]:
        async with self._ops.read_ops() as r:
            result = await r.batch_query_in_global(sa.select(ReplicaGroupRow), querier)
            return [row.ReplicaGroupRow.to_scaling_scheduling_view() for row in result.rows]

    async def fetch_scaling_reconcile_views(
        self,
        querier: BatchQuerier,
        category: ReplicaGroupHandlerCategory,
    ) -> ScalingReconcileFetch:
        async with self._db.begin_readonly_session_read_committed() as db_sess:
            now = (await db_sess.execute(sa.select(sa.func.now()))).scalar_one()
            group_result = await execute_batch_querier(db_sess, sa.select(ReplicaGroupRow), querier)
            group_rows: list[ReplicaGroupRow] = [row.ReplicaGroupRow for row in group_result.rows]
            group_ids = [group_row.id for group_row in group_rows]
            counts = await self._count_live_serving_by_revision(db_sess, group_ids)
            last_histories = await self._latest_history_by_group(db_sess, group_ids, category)
            empty = RevisionReplicaCount(live=0, serving=0)
            views: list[ReplicaGroupScalingReconcileView] = []
            for group_row in group_rows:
                group_counts = counts.get(group_row.id, {})
                current_counts = (
                    group_counts.get(group_row.current_revision_id, empty)
                    if group_row.current_revision_id is not None
                    else empty
                )
                target_counts = (
                    group_counts.get(group_row.target_revision_id, empty)
                    if group_row.target_revision_id is not None
                    else empty
                )
                history_row = last_histories.get(group_row.id)
                last_history = (
                    LastHistory(
                        phase=history_row.phase,
                        attempts=history_row.attempts,
                        started_at=history_row.created_at,
                    )
                    if history_row is not None
                    else None
                )
                views.append(
                    ReplicaGroupScalingReconcileView(
                        group_id=group_row.id,
                        deployment_id=group_row.deployment_id,
                        current_revision_id=group_row.current_revision_id,
                        target_revision_id=group_row.target_revision_id,
                        scaling_status=group_row.scaling_status,
                        desired_current_replica_count=group_row.desired_current_replica_count,
                        desired_target_replica_count=group_row.desired_target_replica_count,
                        current_live_replica_count=current_counts.live,
                        current_serving_replica_count=current_counts.serving,
                        target_live_replica_count=target_counts.live,
                        target_serving_replica_count=target_counts.serving,
                        last_history=last_history,
                    )
                )
            return ScalingReconcileFetch(views=views, now=now)

    async def _latest_history_by_group(
        self,
        db_sess: SASession,
        group_ids: Sequence[ReplicaGroupID],
        category: ReplicaGroupHandlerCategory,
    ) -> Mapping[ReplicaGroupID, ReplicaGroupHistoryRow]:
        if not group_ids:
            return {}
        query = (
            sa.select(ReplicaGroupHistoryRow)
            .where(ReplicaGroupHistoryConditions.by_replica_group_ids(group_ids)())
            .where(ReplicaGroupHistoryConditions.by_category(category)())
            .order_by(
                ReplicaGroupHistoryRow.replica_group_id,
                ReplicaGroupHistoryRow.created_at.desc(),
            )
            .distinct(ReplicaGroupHistoryRow.replica_group_id)
        )
        rows = (await db_sess.execute(query)).scalars().all()
        return {row.replica_group_id: row for row in rows}

    async def _count_live_serving_by_revision(
        self,
        db_sess: SASession,
        group_ids: Sequence[ReplicaGroupID],
    ) -> Mapping[ReplicaGroupID, Mapping[DeploymentRevisionID, RevisionReplicaCount]]:
        if not group_ids:
            return {}
        serving = sa.and_(
            RoutingRow.status == RouteStatus.RUNNING,
            RoutingRow.traffic_status == RouteTrafficStatus.ACTIVE,
        )
        live = sa.or_(RoutingRow.status == RouteStatus.PROVISIONING, serving)
        query = (
            sa.select(
                RoutingRow.replica_group_id,
                RoutingRow.revision,
                sa.func.count().filter(live).label("live"),
                sa.func.count().filter(serving).label("serving"),
            )
            .where(
                RoutingRow.replica_group_id.in_(group_ids),
                RoutingRow.status.in_((RouteStatus.PROVISIONING, RouteStatus.RUNNING)),
            )
            .group_by(RoutingRow.replica_group_id, RoutingRow.revision)
        )
        result = await db_sess.execute(query)
        counts: dict[ReplicaGroupID, dict[DeploymentRevisionID, RevisionReplicaCount]] = {}
        for row in result:
            group_counts = counts.setdefault(ReplicaGroupID(row.replica_group_id), {})
            group_counts[DeploymentRevisionID(row.revision)] = RevisionReplicaCount(
                live=row.live, serving=row.serving
            )
        return counts

    async def update_replica_groups(
        self,
        updaters: Sequence[Updater[ReplicaGroupRow]],
    ) -> BulkUpdaterResult[ReplicaGroupRow]:
        async with self._ops.write_ops() as w:
            return await w.bulk_update_partial(updaters)

    async def apply_scaling_reconcile(
        self,
        apply: ReplicaGroupScalingReconcileApply,
    ) -> None:
        async with self._db.begin_readonly_session_read_committed() as read_sess:
            creators = await self._build_route_creators(read_sess, apply.create_instructions)
            drain_updater = await self._build_drain_updater(read_sess, apply.drain_instructions)
        async with self._ops.write_ops() as w:
            if creators:
                await w.bulk_create_scoped(creators)
            if drain_updater is not None:
                await w.batch_update(drain_updater)
            await w.bulk_apply_transitions([
                self._to_ops_transition(transition) for transition in apply.transitions
            ])

    def _to_ops_transition(
        self,
        transition: ReplicaGroupReconcileTransition,
    ) -> Transition[ReplicaGroupRow, ReplicaGroupHistoryRow]:
        spec = transition.history_spec
        return Transition(
            new_history=Creator(spec=spec),
            match_conditions=[
                ReplicaGroupHistoryConditions.by_replica_group_ids([spec.replica_group_id]),
                ReplicaGroupHistoryConditions.by_category(spec.category),
            ],
            status_updater=transition.status_updater,
        )

    async def _build_route_creators(
        self,
        db_sess: SASession,
        instructions: Sequence[GroupRouteCreateInstruction],
    ) -> list[RBACEntityCreator[RoutingRow]]:
        if not instructions:
            return []
        deployment_ids = {instruction.deployment_id for instruction in instructions}
        revision_ids = {instruction.revision_id for instruction in instructions}
        metadata = await self._deployment_route_metadata(db_sess, deployment_ids)
        health_checks = await self._revision_health_checks(db_sess, revision_ids)
        creators: list[RBACEntityCreator[RoutingRow]] = []
        for instruction in instructions:
            session_owner_id, domain, project_id = metadata[instruction.deployment_id]
            health_check = health_checks.get(instruction.revision_id)
            for _ in range(instruction.count):
                spec = RouteCreatorSpec(
                    deployment_id=instruction.deployment_id,
                    session_owner_id=session_owner_id,
                    domain=domain,
                    project_id=project_id,
                    revision_id=instruction.revision_id,
                    health_check=health_check,
                    replica_group_id=instruction.replica_group_id,
                    traffic_status=RouteTrafficStatus.INACTIVE,
                )
                creators.append(
                    RBACEntityCreator(
                        spec=spec,
                        element_type=RBACElementType.ROUTING,
                        scope_ref=RBACElementRef(
                            element_type=RBACElementType.MODEL_DEPLOYMENT,
                            element_id=str(instruction.deployment_id),
                        ),
                    )
                )
        return creators

    async def _build_drain_updater(
        self,
        db_sess: SASession,
        drain_instructions: Sequence[GroupRouteDrainInstruction],
    ) -> BatchUpdater[RoutingRow] | None:
        route_ids: list[UUID] = []
        for drain in drain_instructions:
            if drain.count <= 0:
                continue
            query = (
                sa.select(RoutingRow.id)
                .where(
                    RoutingRow.replica_group_id == drain.replica_group_id,
                    RoutingRow.revision == drain.revision_id,
                    RoutingRow.status == RouteStatus.RUNNING,
                    RoutingRow.traffic_status == RouteTrafficStatus.ACTIVE,
                )
                .order_by(RoutingRow.created_at.desc())
                .limit(drain.count)
            )
            result = await db_sess.execute(query)
            route_ids.extend(result.scalars().all())
        if not route_ids:
            return None
        return BatchUpdater(
            spec=RouteBatchUpdaterSpec(
                traffic_status=OptionalState.update(RouteTrafficStatus.INACTIVE)
            ),
            conditions=[RouteConditions.by_ids(route_ids)],
        )

    async def _deployment_route_metadata(
        self,
        db_sess: SASession,
        deployment_ids: set[DeploymentID],
    ) -> Mapping[DeploymentID, tuple[UUID, str, UUID]]:
        if not deployment_ids:
            return {}
        query = sa.select(
            EndpointRow.id,
            EndpointRow.session_owner,
            EndpointRow.domain,
            EndpointRow.project,
        ).where(EndpointRow.id.in_(deployment_ids))
        result = await db_sess.execute(query)
        return {
            DeploymentID(row.id): (row.session_owner, row.domain, row.project) for row in result
        }

    async def _revision_health_checks(
        self,
        db_sess: SASession,
        revision_ids: set[DeploymentRevisionID],
    ) -> Mapping[DeploymentRevisionID, ModelHealthCheck | None]:
        if not revision_ids:
            return {}
        query = sa.select(
            DeploymentRevisionRow.id,
            DeploymentRevisionRow.model_definition,
        ).where(DeploymentRevisionRow.id.in_(revision_ids))
        result = await db_sess.execute(query)
        return {
            DeploymentRevisionID(revision_id): (
                model_definition.health_check_config() if model_definition is not None else None
            )
            for revision_id, model_definition in result.all()
        }
