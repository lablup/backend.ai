from __future__ import annotations

import uuid
from typing import TYPE_CHECKING, List, Optional, Sequence

import graphene
import sqlalchemy as sa
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import relationship
from sqlalchemy.orm.exc import NoResultFound

from ..api.exceptions import EndpointNotFound
from .base import GUID, Base, EndpointIDColumn, Item, PaginatedList, ResourceSlotColumn
from .image import ImageRow
from .routing import Routing

if TYPE_CHECKING:
    from sqlalchemy.engine import Row

    from .gql import GraphQueryContext

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

    resource_slots = sa.Column("resource_slots", ResourceSlotColumn(), nullable=True, default="{}")
    url = sa.Column("url", sa.String(length=1024), nullable=False, unique=True)

    routings = relationship("RoutingRow", back_populates="endpoint")
    image = relationship("ImageRow", back_populates="endpoints")

    @classmethod
    async def get(cls, db_session: AsyncSession, endpoint_id: uuid.UUID) -> "EndpointRow":
        """
        :raises: ai.backend.manager.api.exceptions.EndpointNotFound
        """
        j = sa.join(EndpointRow, ImageRow, EndpointRow.image_id == ImageRow.id)
        query = (
            sa.select(Endpoint, ImageRow.name).select_from(j).where(EndpointRow.id == endpoint_id)
        )
        endpoint_row = (await db_session.execute(query)).scalars().first()
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
    image = graphene.String()
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
        ctx: GraphQueryContext,
        row: Row,
    ) -> "Endpoint":
        image_ref = getattr(row, "image_name")
        row = row.EndpointRow
        return cls(
            endpoint_id=row.id,
            image_id=row.image_id,
            image=image_ref,
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
        ctx: GraphQueryContext,
        *,
        project: uuid.UUID | None = None,
    ) -> int:
        query = sa.select([sa.func.count()]).select_from(EndpointRow)
        if project is not None:
            query = query.where(EndpointRow.project == project)
        async with ctx.db.begin_readonly_session() as db_sess:
            result = await db_sess.execute(query)
            return result.scalar()

    @classmethod
    async def load_slice(
        cls,
        ctx: GraphQueryContext,
        limit: int,
        offset: int,
        *,
        project: Optional[uuid.UUID] = None,
        filter: Optional[str] = None,
        order: Optional[str] = None,
    ) -> Sequence["Endpoint"]:
        j = sa.join(EndpointRow, ImageRow, EndpointRow.image_id == ImageRow.id)
        query = (
            sa.select(EndpointRow, ImageRow.name.label("image_name"))
            .select_from(j)
            .limit(limit)
            .offset(offset)
        )
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
        async with ctx.db.begin_readonly_session() as db_sess:
            return [await cls.from_row(ctx, row) async for row in (await db_sess.stream(query))]

    @classmethod
    async def load_all(
        cls,
        ctx: GraphQueryContext,
        *,
        project: uuid.UUID | None = None,
    ) -> Sequence["Endpoint"]:
        async with ctx.db.begin_readonly_session() as session:
            rows = await EndpointRow.list(session, project=project)
        return [await Endpoint.from_row(ctx, row) for row in rows]

    @classmethod
    async def load_item(
        cls,
        ctx: GraphQueryContext,
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
