import uuid
from typing import TYPE_CHECKING, Any, List, Mapping, Optional, Sequence

import graphene
import sqlalchemy as sa
import yarl
from sqlalchemy.dialects import postgresql as pgsql
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import relationship, selectinload
from sqlalchemy.orm.exc import NoResultFound

from ai.backend.common.types import ClusterMode

from ..api.exceptions import EndpointNotFound
from .base import GUID, Base, EndpointIDColumn, Item, PaginatedList, ResourceSlotColumn, URLColumn
from .image import ImageRow
from .routing import Routing

if TYPE_CHECKING:
    pass  # from .gql import GraphQueryContext

__all__ = ("EndpointRow", "Endpoint", "EndpointList")


class EndpointRow(Base):
    __tablename__ = "endpoints"

    id = EndpointIDColumn()
    name = sa.Column("name", sa.String(length=512), nullable=False, unique=True)
    created_user = sa.Column(
        "created_user", GUID, sa.ForeignKey("users.uuid", ondelete="RESTRICT"), nullable=False
    )
    session_owner = sa.Column(
        "session_owner", GUID, sa.ForeignKey("users.uuid", ondelete="RESTRICT"), nullable=False
    )
    # minus session count means this endpoint is requested for removal
    desired_session_count = sa.Column(
        "desired_session_count", sa.Integer, nullable=False, default=0, server_default="0"
    )
    image = sa.Column(
        "image", GUID, sa.ForeignKey("images.id", ondelete="RESTRICT"), nullable=False
    )
    model = sa.Column(
        "model", GUID, sa.ForeignKey("vfolders.id", ondelete="RESTRICT"), nullable=False
    )
    model_mount_destiation = sa.Column(
        "model_mount_destiation",
        sa.String(length=1024),
        nullable=False,
        default="/models",
        server_default="/models",
    )
    domain = sa.Column(
        "domain",
        sa.String(length=64),
        sa.ForeignKey("domains.name", ondelete="RESTRICT"),
        nullable=False,
    )
    project = sa.Column(
        "project",
        GUID,
        sa.ForeignKey("groups.id", ondelete="RESTRICT"),
        nullable=False,
    )
    resource_group = sa.Column(
        "resource_group",
        sa.ForeignKey("scaling_groups.name", ondelete="RESTRICT"),
        index=True,
        nullable=False,
    )
    tag = sa.Column("tag", sa.String(length=64), nullable=True)
    startup_command = sa.Column("startup_command", sa.Text, nullable=True)
    bootstrap_script = sa.Column("bootstrap_script", sa.String(length=16 * 1024), nullable=True)
    callback_url = sa.Column("callback_url", URLColumn, nullable=True, default=sa.null())
    environ = sa.Column("environ", pgsql.JSONB(), nullable=True, default={})
    open_to_public = sa.Column("open_to_public", sa.Boolean, default=False)

    resource_slots = sa.Column("resource_slots", ResourceSlotColumn(), nullable=False)
    url = sa.Column("url", sa.String(length=1024), unique=True)
    resource_opts = sa.Column("resource_opts", pgsql.JSONB(), nullable=True, default={})
    cluster_mode = sa.Column(
        "cluster_mode",
        sa.String(length=16),
        nullable=False,
        default=ClusterMode.SINGLE_NODE,
        server_default=ClusterMode.SINGLE_NODE.name,
    )
    cluster_size = sa.Column(
        "cluster_size", sa.Integer, nullable=False, default=1, server_default="1"
    )

    routings = relationship("RoutingRow", back_populates="endpoint_row")
    image_row = relationship("ImageRow", back_populates="endpoints")

    def __init__(
        self,
        name: str,
        created_user: uuid.UUID,
        session_owner: uuid.UUID,
        desired_session_count: int,
        image: ImageRow,
        model: uuid.UUID,
        domain: str,
        project: uuid.UUID,
        resource_group: str,
        resource_slots: Mapping[str, Any],
        cluster_mode: ClusterMode,
        cluster_size: int,
        model_mount_destination: Optional[str] = None,
        tag: Optional[str] = None,
        startup_command: Optional[str] = None,
        bootstrap_script: Optional[str] = None,
        callback_url: Optional[yarl.URL] = None,
        environ: Optional[Mapping[str, Any]] = None,
        resource_opts: Optional[Mapping[str, Any]] = None,
        open_to_public=False,
    ):
        self.id = uuid.uuid4()
        self.name = name
        self.created_user = created_user
        self.session_owner = session_owner
        self.desired_session_count = desired_session_count
        self.image = image.id
        self.model = model
        self.domain = domain
        self.project = project
        self.resource_group = resource_group
        self.resource_slots = resource_slots
        self.cluster_mode = cluster_mode.name
        self.cluster_size = cluster_size
        self.model_mount_destination = model_mount_destination
        self.tag = tag
        self.startup_command = startup_command
        self.bootstrap_script = bootstrap_script
        self.callback_url = callback_url
        self.environ = environ
        self.resource_opts = resource_opts
        self.open_to_public = open_to_public

    @classmethod
    async def get(
        cls, session: AsyncSession, endpoint_id: uuid.UUID, load_routes=False, load_image=False
    ) -> "EndpointRow":
        """
        :raises: sqlalchemy.orm.exc.NoResultFound
        """
        query = sa.select(EndpointRow).filter(EndpointRow.id == endpoint_id)
        if load_routes:
            query = query.options(selectinload(EndpointRow.routings))
        if load_image:
            query = query.options(selectinload(EndpointRow.image_row))
        result = await session.execute(query)
        row = result.scalar()
        if row is None:
            raise NoResultFound
        return row

    @classmethod
    async def list(
        cls,
        session: AsyncSession,
        project: uuid.UUID | None = None,
        load_routes=False,
        load_image=False,
    ) -> List["EndpointRow"]:
        query = sa.select(EndpointRow)
        if load_routes:
            query = query.options(selectinload(EndpointRow.routings))
        if load_image:
            query = query.options(selectinload(EndpointRow.image_row))

        if project:
            query = query.filter(EndpointRow.project == project)
        result = await session.execute(query)
        return result.scalars().all()


class Endpoint(graphene.ObjectType):
    class Meta:
        interfaces = (Item,)

    endpoint_id = graphene.UUID()
    image = graphene.String()
    model = graphene.UUID()
    domain = graphene.String()
    project = graphene.UUID()
    resource_group = graphene.String()
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
            image=row.image_row.image,
            model=row.model,
            domain=row.domain,
            project=row.project,
            resource_group=row.resource_group,
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
