"""Database source for replica group repository operations."""

from __future__ import annotations

import logging
from collections.abc import Mapping, Sequence
from typing import TYPE_CHECKING

import sqlalchemy as sa

from ai.backend.common.identifier.deployment_revision import DeploymentRevisionID
from ai.backend.common.identifier.replica_group import ReplicaGroupID
from ai.backend.logging.utils import BraceStyleAdapter
from ai.backend.manager.data.deployment.types import (
    ReplicaGroupHandlerCategory,
    ReplicaGroupLastHistory,
    RouteStatus,
    RouteTrafficStatus,
)
from ai.backend.manager.models.replica_group import ReplicaGroupRow
from ai.backend.manager.models.replica_group_history import ReplicaGroupHistoryRow
from ai.backend.manager.models.routing import RoutingRow
from ai.backend.manager.models.utils import ExtendedAsyncSAEngine
from ai.backend.manager.repositories.base import BatchQuerier, execute_batch_querier
from ai.backend.manager.repositories.base.rbac.entity_creator import (
    execute_rbac_entity_creators,
)
from ai.backend.manager.repositories.base.updater import (
    BulkUpdaterResult,
    Updater,
    execute_batch_updater,
    execute_updater,
)
from ai.backend.manager.repositories.ops.provider import DBOpsProvider
from ai.backend.manager.repositories.replica_group.types import (
    ReplicaGroupScalingReconcileApply,
    RevisionReplicaCount,
)
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
    _ops: DBOpsProvider

    def __init__(self, db: ExtendedAsyncSAEngine) -> None:
        self._db = db
        self._ops = DBOpsProvider(db)

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
    ) -> list[ReplicaGroupScalingReconcileView]:
        async with self._db.begin_readonly_session_read_committed() as db_sess:
            group_result = await execute_batch_querier(db_sess, sa.select(ReplicaGroupRow), querier)
            group_rows: list[ReplicaGroupRow] = [row.ReplicaGroupRow for row in group_result.rows]
            group_ids = [group_row.id for group_row in group_rows]
            counts = await self._count_live_serving_by_revision(db_sess, group_ids)
            last_histories = await self._last_histories(
                db_sess, group_ids, ReplicaGroupHandlerCategory.SCALING
            )
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
                views.append(
                    ReplicaGroupScalingReconcileView(
                        group_id=group_row.id,
                        deployment_id=group_row.deployment_id,
                        current_revision_id=group_row.current_revision_id,
                        target_revision_id=group_row.target_revision_id,
                        desired_current_replica_count=group_row.desired_current_replica_count,
                        desired_target_replica_count=group_row.desired_target_replica_count,
                        current_live_replica_count=current_counts.live,
                        current_serving_replica_count=current_counts.serving,
                        target_live_replica_count=target_counts.live,
                        target_serving_replica_count=target_counts.serving,
                        last_history=last_histories.get(group_row.id),
                    )
                )
            return views

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

    async def _last_histories(
        self,
        db_sess: SASession,
        group_ids: Sequence[ReplicaGroupID],
        category: ReplicaGroupHandlerCategory,
    ) -> Mapping[ReplicaGroupID, ReplicaGroupLastHistory]:
        if not group_ids:
            return {}
        query = (
            sa.select(ReplicaGroupHistoryRow)
            .where(
                ReplicaGroupHistoryRow.replica_group_id.in_(group_ids),
                ReplicaGroupHistoryRow.category == category,
            )
            .distinct(ReplicaGroupHistoryRow.replica_group_id)
            .order_by(
                ReplicaGroupHistoryRow.replica_group_id,
                ReplicaGroupHistoryRow.created_at.desc(),
            )
        )
        result = await db_sess.execute(query)
        return {
            row.replica_group_id: ReplicaGroupLastHistory(
                id=row.id,
                category=row.category,
                phase=row.phase,
                attempts=row.attempts,
                started_at=row.created_at,
                error_code=row.error_code,
                to_status=row.to_status,
            )
            for row in result.scalars().all()
        }

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
        async with self._db.begin_session_read_committed() as db_sess:
            if apply.scale_out_creators:
                await execute_rbac_entity_creators(db_sess, apply.scale_out_creators)
            if apply.drain_updater is not None:
                await execute_batch_updater(db_sess, apply.drain_updater)
            for updater in apply.group_updaters:
                await execute_updater(db_sess, updater)
            if apply.merge_history_ids:
                await db_sess.execute(
                    sa.update(ReplicaGroupHistoryRow)
                    .where(ReplicaGroupHistoryRow.id.in_(apply.merge_history_ids))
                    .values(attempts=ReplicaGroupHistoryRow.attempts + 1)
                )
            if apply.new_history_specs:
                db_sess.add_all([spec.build_row() for spec in apply.new_history_specs])
                await db_sess.flush()
