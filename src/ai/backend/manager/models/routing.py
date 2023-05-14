import logging
import uuid
from enum import Enum
from typing import TYPE_CHECKING, Sequence

import graphene
import sqlalchemy as sa
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import relationship, selectinload
from sqlalchemy.orm.exc import NoResultFound

from ai.backend.common.logging_utils import BraceStyleAdapter

from ..api.exceptions import RoutingNotFound
from .base import GUID, Base, EnumValueType, IDColumn, Item, PaginatedList

if TYPE_CHECKING:
    # from .gql import GraphQueryContext
    pass


__all__ = ("RoutingRow", "Routing", "RoutingList", "RouteStatus")


log = BraceStyleAdapter(logging.getLogger(__spec__.name))  # type: ignore


class RouteStatus(Enum):
    HEALTHY = "healthy"
    UNHEALTHY = "unhealthy"
    PROVISIONING = "provisioning"
    FAILED_TO_START = "failed_to_start"


class RoutingRow(Base):
    __tablename__ = "routings"
    __table_args__ = (
        sa.UniqueConstraint("endpoint", "session", name="uq_routings_endpoint_session"),
    )

    id = IDColumn("id")
    endpoint = sa.Column(
        "endpoint", GUID, sa.ForeignKey("endpoints.id", ondelete="CASCADE"), nullable=False
    )
    session = sa.Column(
        "session", GUID, sa.ForeignKey("sessions.id", ondelete="RESTRICT"), nullable=False
    )
    status = sa.Column(
        "status",
        EnumValueType(RouteStatus),
        nullable=False,
        default=RouteStatus.PROVISIONING,
    )

    traffic_ratio = sa.Column("traffic_ratio", sa.Float(), nullable=False)

    endpoint_row = relationship("EndpointRow", back_populates="routings")
    session_row = relationship("SessionRow", back_populates="routing")

    @classmethod
    async def get_by_session(
        cls, db_sess: AsyncSession, session_id: uuid.UUID, load_endpoint=False
    ) -> "RoutingRow":
        """
        :raises: sqlalchemy.orm.exc.NoResultFound
        """
        query = sa.select(RoutingRow).where(RoutingRow.session == session_id)
        if load_endpoint:
            query = query.options(selectinload(RoutingRow.endpoint_row))
        result = await db_sess.execute(query)
        row = result.scalar()
        if row is None:
            raise NoResultFound
        return row

    @classmethod
    async def get(
        cls, db_sess: AsyncSession, route_id: uuid.UUID, load_session=False, load_endpoint=False
    ) -> "RoutingRow":
        """
        :raises: sqlalchemy.orm.exc.NoResultFound
        """
        query = sa.select(RoutingRow).where(RoutingRow.id == route_id)
        if load_session:
            query = query.options(selectinload(RoutingRow.session_row))
        if load_endpoint:
            query = query.options(selectinload(RoutingRow.endpoint_row))
        result = await db_sess.execute(query)
        row = result.scalar()
        if row is None:
            raise NoResultFound
        return row

    def __init__(
        self,
        endpoint: uuid.UUID,
        session: uuid.UUID,
        status=RouteStatus.PROVISIONING,
        traffic_ratio=1.0,
    ) -> None:
        self.endpoint = endpoint
        self.session = session
        self.status = status
        self.traffic_ratio = traffic_ratio


class Routing(graphene.ObjectType):
    class Meta:
        interfaces = (Item,)

    routing_id = graphene.UUID()
    endpoint = graphene.String()
    session = graphene.UUID()
    traffic_ratio = graphene.Float()

    @classmethod
    async def from_row(
        cls,
        ctx,  # ctx: GraphQueryContext,
        row: RoutingRow,
    ) -> "Routing":
        return cls(
            routing_id=row.id,
            endpoint=row.endpoint_row.url,
            session=row.session,
            traffic_ratio=row.traffic_ratio,
        )

    @classmethod
    async def load_count(
        cls,
        ctx,  # ctx: GraphQueryContext,
        *,
        endpoint_id: uuid.UUID | None = None,
    ) -> int:
        query = sa.select([sa.func.count()]).select_from(RoutingRow)
        if endpoint_id is not None:
            query = query.where(RoutingRow.endpoint == endpoint_id)
        async with ctx.db.begin_readonly() as conn:
            result = await conn.execute(query)
            return result.scalar()

    @classmethod
    async def load_slice(
        cls,
        ctx,  # ctx: GraphQueryContext,
        limit: int,
        offset: int,
        *,
        endpoint_id: uuid.UUID | None = None,
        filter: str | None = None,
        order: str | None = None,
    ) -> Sequence["Routing"]:
        query = sa.select(RoutingRow).limit(limit).offset(offset)
        if endpoint_id is not None:
            query = query.where(RoutingRow.endpoint == endpoint_id)
        """
        if filter is not None:
            parser = QueryFilterParser(cls._queryfilter_fieldspec)
            query = parser.append_filter(query, filter)
        if order is not None:
            parser = QueryOrderParser(cls._queryorder_colmap)
            query = parser.append_ordering(query, order)
        """
        async with ctx.db.begin_readonly_session() as session:
            return [await cls.from_row(ctx, row) async for row in (await session.stream(query))]

    @classmethod
    async def load_all(
        cls, ctx, *, endpoint_id: uuid.UUID | None = None  # ctx: GraphQueryContext,
    ) -> Sequence["Routing"]:
        async with ctx.db.begin_readonly_session() as session:
            rows = await RoutingRow.list(session, endpoint_id=endpoint_id)
        return [await Routing.from_row(ctx, row) for row in rows]

    @classmethod
    async def load_item(
        cls,
        ctx,  # ctx: GraphQueryContext,
        *,
        routing_id: uuid.UUID,
    ) -> "Routing":
        try:
            async with ctx.db.begin_readonly_session() as session:
                row = await RoutingRow.get(session, routing_id)
        except NoResultFound:
            raise RoutingNotFound
        return await Routing.from_row(ctx, row)


class RoutingList(graphene.ObjectType):
    class Meta:
        interfaces = (PaginatedList,)

    items = graphene.List(Routing, required=True)
