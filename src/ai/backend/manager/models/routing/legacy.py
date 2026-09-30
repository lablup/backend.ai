"""Routing reads only the gql_legacy paths use. Delete this file together with gql_legacy."""

from __future__ import annotations

import uuid
from collections.abc import Sequence

import sqlalchemy as sa
from sqlalchemy.exc import NoResultFound
from sqlalchemy.ext.asyncio import AsyncSession

from ai.backend.manager.data.deployment.types import RouteStatus
from ai.backend.manager.models.routing.row import RoutingRow

__all__ = (
    "get_routing",
    "list_routings",
)


async def list_routings(
    db_sess: AsyncSession,
    endpoint_id: uuid.UUID,
    project: uuid.UUID | None = None,
    domain: str | None = None,
    user_uuid: uuid.UUID | None = None,
) -> Sequence[RoutingRow]:
    """Used only by Routing.load_all, which nothing calls."""
    query = (
        sa.select(RoutingRow)
        .filter(RoutingRow.endpoint == endpoint_id)
        .filter(RoutingRow.status.in_(list(RouteStatus.active_route_statuses())))
        .order_by(sa.desc(RoutingRow.created_at))
    )
    if project:
        query = query.filter(RoutingRow.project == project)
    if domain:
        query = query.filter(RoutingRow.domain == domain)
    if user_uuid:
        query = query.filter(RoutingRow.session_owner == user_uuid)
    result = await db_sess.execute(query)
    return result.scalars().all()


async def get_routing(
    db_sess: AsyncSession,
    route_id: uuid.UUID,
    project: uuid.UUID | None = None,
    domain: str | None = None,
    user_uuid: uuid.UUID | None = None,
) -> RoutingRow:
    """
    :raises: sqlalchemy.orm.exc.NoResultFound
    """
    query = sa.select(RoutingRow).where(RoutingRow.id == route_id)
    if project:
        query = query.filter(RoutingRow.project == project)
    if domain:
        query = query.filter(RoutingRow.domain == domain)
    if user_uuid:
        query = query.filter(RoutingRow.session_owner == user_uuid)
    result = await db_sess.execute(query)
    row = result.scalar()
    if row is None:
        raise NoResultFound
    return row
