import uuid
from typing import TYPE_CHECKING, List, Optional, Sequence

import graphene
import sqlalchemy as sa
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import relationship
from sqlalchemy.orm.exc import NoResultFound

from ..api.exceptions import EndpointNotFound
from .base import GUID, Base, EndpointIDColumn, Item, PaginatedList, ResourceSlotColumn
from .routing import Routing

if TYPE_CHECKING:
    pass  # from .gql import GraphQueryContext

__all__ = ("EndpointRow", "Endpoint", "EndpointList")


class EndpointRow(Base):
    __tablename__ = "endpoints"

    id = EndpointIDColumn()
    image_id = sa.Column(
        "image_id", GUID, sa.ForeignKey("images.id", ondelete="RESTRICT"), nullable=False
    )
    model_id = sa.Column(
        "model_id", GUID, sa.ForeignKey("vfolders.id", ondelete="RESTRICT"), nullable=False
    )
    domain_name = sa.Column(
        "domain_name",
        sa.String(length=64),
        sa.ForeignKey("domains.name", ondelete="RESTRICT"),
        nullable=False,
    )
    project_id = sa.Column(
        "project_id",
        GUID,
        sa.ForeignKey("groups.id", ondelete="RESTRICT"),
        nullable=False,
    )
    resource_group_name = sa.Column(
        "resource_group_name",
        sa.ForeignKey("scaling_groups.name", ondelete="RESTRICT"),
        index=True,
        nullable=False,
    )

    resource_slots = sa.Column("resource_slots", ResourceSlotColumn(), nullable=False)
    url = sa.Column("url", sa.String(length=1024), nullable=False, unique=True)

    routings = relationship("RoutingRow", back_populates="endpoint")
    image = relationship("ImageRow", back_populates="endpoints")

    @classmethod
    async def get(cls, session: AsyncSession, endpoint_id: uuid.UUID) -> "EndpointRow":
        """
        :raises: ai.backend.manager.api.exceptions.EndpointNotFound
        """
        endpoint_row = await session.get(EndpointRow, endpoint_id)
        if endpoint_row is None:
            raise EndpointNotFound()
        return endpoint_row

    @classmethod
    async def list(
        cls, session: AsyncSession, project: uuid.UUID | None = None
    ) -> List["EndpointRow"]:
        query = sa.select(EndpointRow)
        if project:
            query = query.where(EndpointRow.project == project)
        result = await session.execute(query)
        return result.scalars().all()


class Endpoint(graphene.ObjectType):
    class Meta:
        interfaces = (Item,)

    endpoint_id = graphene.UUID()
    image_id = graphene.String()
    model_id = graphene.UUID()
    domain_name = graphene.String()
    project_id = graphene.UUID()
    resource_group_name = graphene.String()
    resource_slots = graphene.JSONString()
    url = graphene.String()
    routings = graphene.List(Routing)

    @classmethod
    async def from_row(
        cls,
        ctx,  # ctx: GraphQueryContext,
        row: EndpointRow,
    ) -> "Endpoint":
        return cls(
            endpoint_id=row.id,
            image_id=row.image_id,
            model_id=row.model_id,
            domain_name=row.domain_name,
            project_id=row.project_id,
            resource_group_name=row.resource_group_name,
            resource_slots=row.resource_slots,
            url=row.url,
            routings=[await Routing.from_row(ctx, routing) for routing in row.routings],
        )

    @classmethod
    async def load_count(
        cls,
        ctx,  # ctx: GraphQueryContext,
        *,
        project: uuid.UUID | None = None,
    ) -> int:
        query = sa.select([sa.func.count()]).select_from(EndpointRow)
        if project is not None:
            query = query.where(EndpointRow.project == project)
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
        project: Optional[uuid.UUID] = None,
        filter: Optional[str] = None,
        order: Optional[str] = None,
    ) -> Sequence["Endpoint"]:
        query = sa.select(EndpointRow).limit(limit).offset(offset)
        if project is not None:
            query = query.where(EndpointRow.project == project)
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
        cls,
        ctx,  # ctx: GraphQueryContext,
        *,
        project: uuid.UUID | None = None,
    ) -> Sequence["Endpoint"]:
        async with ctx.db.begin_readonly_session() as session:
            rows = await EndpointRow.list(session, project=project)
        return [await Endpoint.from_row(ctx, row) for row in rows]

    @classmethod
    async def load_item(
        cls,
        ctx,  # ctx: GraphQueryContext,
        *,
        endpoint_id: uuid.UUID,
    ) -> "Endpoint":
        """
        :raises: ai.backend.manager.api.exceptions.EndpointNotFound
        """
        try:
            async with ctx.db.begin_readonly_session() as session:
                row = await EndpointRow.get(session, endpoint_id=endpoint_id)
        except NoResultFound:
            raise EndpointNotFound
        return await Endpoint.from_row(ctx, row)


class EndpointList(graphene.ObjectType):
    class Meta:
        interfaces = (PaginatedList,)

    items = graphene.List(Endpoint, required=True)
