import uuid
from typing import TYPE_CHECKING, Sequence

import graphene
import sqlalchemy as sa
from sqlalchemy.dialects import postgresql as psql
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import relationship
from sqlalchemy.orm.exc import NoResultFound

from ..api.exceptions import RoutingNotFound
from .base import GUID, Base, IDColumn, Item, PaginatedList
from .utils import ExtendedAsyncSAEngine, execute_with_retry

if TYPE_CHECKING:
    # from .gql import GraphQueryContext
    pass


__all__ = ("RoutingRow", "Routing", "RoutingList")


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

    traffic_ratio = sa.Column("traffic_ratio", sa.Float(), nullable=False)

    endpoint_row = relationship("EndpointRow", back_populates="routings")

    @classmethod
    async def get(cls, session: AsyncSession, routing_id: uuid.UUID) -> "RoutingRow":
        """
        :raises: sqlalchemy.orm.exc.NoResultFound
        """
        query = sa.select(RoutingRow).filter(RoutingRow.id == routing_id)
        result = await session.execute(query)
        try:
            return result.one()
        except NoResultFound:
            raise

    @classmethod
    async def create(
        cls,
        engine: ExtendedAsyncSAEngine,
        endpoint_id: uuid.UUID,
        session_id: uuid.UUID,
        traffic_ratio: float = 100.0,
    ) -> uuid.UUID:
        # https://docs.sqlalchemy.org/en/14/dialects/postgresql.html#sqlalchemy.dialects.postgresql.Insert.on_conflict_do_nothing

        async def _create_routing() -> uuid.UUID:
            async with engine.begin_session() as db_sess:
                routing_id = uuid.uuid4()
                query = (
                    psql.insert(RoutingRow)
                    .values(
                        id=routing_id,
                        endpoint=endpoint_id,
                        session=session_id,
                        traffic_ratio=traffic_ratio,
                    )
                    .on_conflict_do_nothing(
                        index_elements=[RoutingRow.endpoint, RoutingRow.session]
                    )
                )
                await db_sess.execute(query)
                return routing_id

        return await execute_with_retry(_create_routing)


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
                row = await RoutingRow.get(session, routing_id=routing_id)
        except NoResultFound:
            raise RoutingNotFound
        return await Routing.from_row(ctx, row)


class RoutingList(graphene.ObjectType):
    class Meta:
        interfaces = (PaginatedList,)

    items = graphene.List(Routing, required=True)
