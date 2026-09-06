"""Replica-group reads the reconcile loop runs beside its own writes.

Each one spans more than the group table -- route counts per revision, the latest
history row, the owning endpoint's settings -- so none of them is a spec the
general read ops execute. They live here so the reconcile loop reaches them
through a provider instead of through an engine of its own, and so every read of
one tick shares the transaction its ``now`` was read in.
"""

from __future__ import annotations

from collections.abc import Mapping, Sequence
from uuid import UUID

import sqlalchemy as sa

from ai.backend.common.data.entity.deployment import DeploymentID
from ai.backend.common.data.entity.deployment_revision import DeploymentRevisionID
from ai.backend.common.data.entity.project import ProjectID
from ai.backend.common.data.entity.replica_group import ReplicaGroupID
from ai.backend.common.data.entity.user import UserID
from ai.backend.manager.data.deployment.types import (
    DeploymentHandlerOptions,
    ReplicaGroupHandlerCategory,
    RouteHealthStatus,
    RouteStatus,
    RouteTrafficStatus,
)
from ai.backend.manager.data.reconciler.types import LastHistory
from ai.backend.manager.models.deployment_revision.row import DeploymentRevisionRow
from ai.backend.manager.models.endpoint.row import EndpointRow
from ai.backend.manager.models.replica_group_history.conditions import (
    ReplicaGroupHistoryConditions,
)
from ai.backend.manager.models.replica_group_history.row import ReplicaGroupHistoryRow
from ai.backend.manager.models.routing.row import RoutingRow
from ai.backend.manager.repositories.ops.v2.base import V2OpsBase
from ai.backend.manager.views.replica_group import (
    DeploymentRolloutContext,
    RevisionReplicaCount,
    RevisionRouteConfig,
)


def _serving_predicate() -> sa.ColumnElement[bool]:
    """RUNNING & traffic ACTIVE -- routes actually receiving traffic."""
    return sa.and_(
        RoutingRow.status == RouteStatus.RUNNING,
        RoutingRow.traffic_status == RouteTrafficStatus.ACTIVE,
    )


def _live_predicate() -> sa.ColumnElement[bool]:
    """PROVISIONING (warming) or serving -- routes counted toward the replica count."""
    return sa.or_(RoutingRow.status == RouteStatus.PROVISIONING, _serving_predicate())


def _scale_in_termination_priority() -> sa.ColumnElement[int]:
    """Scale-in drain order (lower drains first): not-yet-serving (PROVISIONING) first,
    then RUNNING by health UNHEALTHY < DEGRADED < NOT_CHECKED < HEALTHY."""
    return sa.case(
        (RoutingRow.status != RouteStatus.RUNNING, 0),
        (RoutingRow.health_status == RouteHealthStatus.UNHEALTHY, 1),
        (RoutingRow.health_status == RouteHealthStatus.DEGRADED, 2),
        (RoutingRow.health_status == RouteHealthStatus.NOT_CHECKED, 3),
        else_=4,
    )


class ReplicaGroupQueryOps(V2OpsBase):
    """The reconcile-side reads, bound to a single session."""

    async def desired_replicas_by_deployment(
        self, deployment_ids: Sequence[DeploymentID]
    ) -> Mapping[DeploymentID, int]:
        """The autoscaling-resolved target per deployment, falling back to the
        user-set replica count when autoscaling has not computed one."""
        if not deployment_ids:
            return {}
        target = sa.func.coalesce(EndpointRow.desired_replicas, EndpointRow.replicas)
        query = sa.select(EndpointRow.id, target.label("target")).where(
            EndpointRow.id.in_(deployment_ids)
        )
        rows = (await self._sess.execute(query)).all()
        return {row.id: row.target for row in rows}

    async def handler_options_by_deployment(
        self, deployment_ids: Sequence[DeploymentID]
    ) -> Mapping[DeploymentID, DeploymentHandlerOptions]:
        if not deployment_ids:
            return {}
        query = sa.select(EndpointRow.id, EndpointRow.options).where(
            EndpointRow.id.in_(deployment_ids)
        )
        rows = (await self._sess.execute(query)).all()
        return {row.id: row.options.handler_options for row in rows}

    async def latest_history_by_group(
        self,
        group_ids: Sequence[ReplicaGroupID],
        category: ReplicaGroupHandlerCategory,
    ) -> Mapping[ReplicaGroupID, LastHistory]:
        """The newest history row of each group within the category."""
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
        rows = (await self._sess.execute(query)).scalars().all()
        return {
            row.replica_group_id: LastHistory(
                phase=row.phase, attempts=row.attempts, started_at=row.created_at
            )
            for row in rows
        }

    async def live_serving_counts_by_revision(
        self, group_ids: Sequence[ReplicaGroupID]
    ) -> Mapping[ReplicaGroupID, Mapping[DeploymentRevisionID, RevisionReplicaCount]]:
        if not group_ids:
            return {}
        serving = _serving_predicate()
        live = _live_predicate()
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
        result = await self._sess.execute(query)
        counts: dict[ReplicaGroupID, dict[DeploymentRevisionID, RevisionReplicaCount]] = {}
        for row in result:
            group_counts = counts.setdefault(ReplicaGroupID(row.replica_group_id), {})
            group_counts[DeploymentRevisionID(row.revision)] = RevisionReplicaCount(
                live=row.live, serving=row.serving
            )
        return counts

    async def rollout_contexts(
        self, deployment_ids: Sequence[DeploymentID]
    ) -> Mapping[DeploymentID, DeploymentRolloutContext]:
        """What each deployment's rollout needs of its endpoint: the group it serves
        traffic from, and the ownership scope a fresh group inherits."""
        if not deployment_ids:
            return {}
        query = sa.select(
            EndpointRow.id,
            EndpointRow.primary_replica_group_id,
            EndpointRow.domain,
            EndpointRow.project,
            EndpointRow.session_owner,
        ).where(EndpointRow.id.in_(deployment_ids))
        return {
            DeploymentID(row.id): DeploymentRolloutContext(
                deployment_id=DeploymentID(row.id),
                primary_replica_group_id=row.primary_replica_group_id,
                domain_name=row.domain,
                project_id=ProjectID(row.project),
                session_owner_id=UserID(row.session_owner),
            )
            for row in (await self._sess.execute(query)).all()
        }

    async def revision_route_configs(
        self, revision_ids: Sequence[DeploymentRevisionID]
    ) -> Mapping[DeploymentRevisionID, RevisionRouteConfig]:
        if not revision_ids:
            return {}
        query = sa.select(
            DeploymentRevisionRow.id,
            DeploymentRevisionRow.model_definition,
            DeploymentRevisionRow.termination_grace_period,
        ).where(DeploymentRevisionRow.id.in_(revision_ids))
        result = await self._sess.execute(query)
        return {
            DeploymentRevisionID(revision_id): RevisionRouteConfig(
                health_check=(
                    model_definition.health_check_setting()
                    if model_definition is not None
                    else None
                ),
                termination_grace_period=termination_grace_period,
            )
            for revision_id, model_definition, termination_grace_period in result.all()
        }

    async def drain_candidate_route_ids(
        self,
        replica_group_id: ReplicaGroupID,
        revision_id: DeploymentRevisionID,
        count: int,
    ) -> list[UUID]:
        """The routes to drain first for a scale-in, in termination priority order.

        Candidates are the live set (the same set the deficit counts): not-yet-serving
        PROVISIONING routes drain before serving RUNNING routes, RUNNING by health.
        """
        query = (
            sa.select(RoutingRow.id)
            .where(
                RoutingRow.replica_group_id == replica_group_id,
                RoutingRow.revision == revision_id,
                _live_predicate(),
            )
            .order_by(_scale_in_termination_priority().asc(), RoutingRow.created_at.asc())
            .limit(count)
        )
        return list((await self._sess.scalars(query)).all())
