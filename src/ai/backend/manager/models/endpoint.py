import datetime
import logging
import uuid
from enum import Enum
from typing import TYPE_CHECKING, Any, Iterable, List, Mapping, Optional, Sequence

import graphene
import jwt
import sqlalchemy as sa
import yarl
from graphene.types.datetime import DateTime as GQLDateTime
from sqlalchemy.dialects import postgresql as pgsql
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import relationship, selectinload
from sqlalchemy.orm.exc import NoResultFound

from ai.backend.common.docker import ImageRef
from ai.backend.common.logging_utils import BraceStyleAdapter
from ai.backend.common.types import ClusterMode, ResourceSlot
from ai.backend.manager.defs import SERVICE_MAX_RETRIES

from ..api.exceptions import EndpointNotFound, EndpointTokenNotFound
from .base import (
    GUID,
    Base,
    EndpointIDColumn,
    EnumValueType,
    ForeignKeyIDColumn,
    IDColumn,
    InferenceSessionError,
    Item,
    PaginatedList,
    ResourceSlotColumn,
    URLColumn,
    set_if_set,
    simple_db_mutate_returning_item,
)
from .image import ImageNode, ImageRefType, ImageRow
from .routing import RouteStatus, Routing
from .user import UserRole

if TYPE_CHECKING:
    from .gql import GraphQueryContext

__all__ = (
    "EndpointRow",
    "Endpoint",
    "EndpointLifecycle",
    "EndpointList",
    "ModifyEndpoint",
    "EndpointTokenRow",
    "EndpointToken",
    "EndpointTokenList",
)


log = BraceStyleAdapter(logging.getLogger(__spec__.name))  # type: ignore


class EndpointLifecycle(Enum):
    CREATED = "created"
    DESTROYING = "destroying"
    DESTROYED = "destroyed"


class EndpointRow(Base):
    __tablename__ = "endpoints"

    id = EndpointIDColumn()
    name = sa.Column("name", sa.String(length=512), nullable=False)
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
        "model",
        GUID,
        sa.ForeignKey("vfolders.id", ondelete="SET NULL"),
        nullable=True,
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
    lifecycle_stage = sa.Column(
        "lifecycle_stage",
        EnumValueType(EndpointLifecycle),
        nullable=False,
        default=EndpointLifecycle.CREATED,
    )
    tag = sa.Column("tag", sa.String(length=64), nullable=True)
    startup_command = sa.Column("startup_command", sa.Text, nullable=True)
    bootstrap_script = sa.Column("bootstrap_script", sa.String(length=16 * 1024), nullable=True)
    callback_url = sa.Column("callback_url", URLColumn, nullable=True, default=sa.null())
    environ = sa.Column("environ", pgsql.JSONB(), nullable=True, default={})
    open_to_public = sa.Column("open_to_public", sa.Boolean, default=False)

    resource_slots = sa.Column("resource_slots", ResourceSlotColumn(), nullable=False)
    url = sa.Column("url", sa.String(length=1024))
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

    retries = sa.Column("retries", sa.Integer, nullable=False, default=0, server_default="0")
    created_at = sa.Column(
        "created_at",
        sa.DateTime(timezone=True),
        server_default=sa.text("now()"),
        nullable=True,
    )
    destroyed_at = sa.Column(
        "destroyed_at",
        sa.DateTime(timezone=True),
        nullable=True,
    )

    routings = relationship("RoutingRow", back_populates="endpoint_row")
    tokens = relationship("EndpointTokenRow", back_populates="endpoint_row")
    image_row = relationship("ImageRow", back_populates="endpoints")
    created_user_row = relationship(
        "UserRow", back_populates="created_endpoints", foreign_keys="EndpointRow.created_user"
    )
    session_owner_row = relationship(
        "UserRow", back_populates="owned_endpoints", foreign_keys="EndpointRow.session_owner"
    )

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
        cls,
        session: AsyncSession,
        endpoint_id: uuid.UUID,
        domain: Optional[str] = None,
        project: Optional[uuid.UUID] = None,
        user_uuid: Optional[uuid.UUID] = None,
        load_routes=False,
        load_tokens=False,
        load_image=False,
        load_created_user=False,
        load_session_owner=False,
    ) -> "EndpointRow":
        """
        :raises: sqlalchemy.orm.exc.NoResultFound
        """
        query = sa.select(EndpointRow).filter(EndpointRow.id == endpoint_id)
        if load_routes:
            query = query.options(selectinload(EndpointRow.routings))
        if load_tokens:
            query = query.options(selectinload(EndpointRow.tokens))
        if load_image:
            query = query.options(selectinload(EndpointRow.image_row))
        if load_created_user:
            query = query.options(selectinload(EndpointRow.created_user_row))
        if load_session_owner:
            query = query.options(selectinload(EndpointRow.session_owner_row))
        if project:
            query = query.filter(EndpointRow.project == project)
        if domain:
            query = query.filter(EndpointRow.domain == domain)
        if user_uuid:
            query = query.filter(EndpointRow.session_owner == user_uuid)
        result = await session.execute(query)
        row = result.scalar()
        if row is None:
            raise NoResultFound
        return row

    @classmethod
    async def list(
        cls,
        session: AsyncSession,
        domain: Optional[str] = None,
        project: Optional[uuid.UUID] = None,
        user_uuid: Optional[uuid.UUID] = None,
        load_routes=False,
        load_image=False,
        load_tokens=False,
        load_created_user=False,
        load_session_owner=False,
        status_filter=[EndpointLifecycle.CREATED],
    ) -> List["EndpointRow"]:
        query = (
            sa.select(EndpointRow)
            .order_by(sa.desc(EndpointRow.created_at))
            .filter(EndpointRow.lifecycle_stage.in_(status_filter))
        )
        if load_routes:
            query = query.options(selectinload(EndpointRow.routings))
        if load_tokens:
            query = query.options(selectinload(EndpointRow.tokens))
        if load_image:
            query = query.options(selectinload(EndpointRow.image_row))
        if load_created_user:
            query = query.options(selectinload(EndpointRow.created_user_row))
        if load_session_owner:
            query = query.options(selectinload(EndpointRow.session_owner_row))
        if project:
            query = query.filter(EndpointRow.project == project)
        if domain:
            query = query.filter(EndpointRow.domain == domain)
        if user_uuid:
            query = query.filter(EndpointRow.session_owner == user_uuid)
        result = await session.execute(query)
        return result.scalars().all()

    @classmethod
    async def list_by_model(
        cls,
        session: AsyncSession,
        model_id: uuid.UUID,
        domain: Optional[str] = None,
        project: Optional[uuid.UUID] = None,
        user_uuid: Optional[uuid.UUID] = None,
        load_routes=False,
        load_image=False,
        load_tokens=False,
        load_created_user=False,
        load_session_owner=False,
        status_filter=[EndpointLifecycle.CREATED],
    ) -> List["EndpointRow"]:
        query = (
            sa.select(EndpointRow)
            .order_by(sa.desc(EndpointRow.created_at))
            .filter(
                EndpointRow.lifecycle_stage.in_(status_filter) & (EndpointRow.model == model_id)
            )
        )
        if load_routes:
            query = query.options(selectinload(EndpointRow.routings))
        if load_tokens:
            query = query.options(selectinload(EndpointRow.tokens))
        if load_image:
            query = query.options(selectinload(EndpointRow.image_row))
        if load_created_user:
            query = query.options(selectinload(EndpointRow.created_user_row))
        if load_session_owner:
            query = query.options(selectinload(EndpointRow.session_owner_row))
        if project:
            query = query.filter(EndpointRow.project == project)
        if domain:
            query = query.filter(EndpointRow.domain == domain)
        if user_uuid:
            query = query.filter(EndpointRow.session_owner == user_uuid)
        result = await session.execute(query)
        return result.scalars().all()


class EndpointTokenRow(Base):
    __tablename__ = "endpoint_tokens"

    id = IDColumn()
    token = sa.Column("token", sa.String(), nullable=False)
    endpoint = sa.Column(
        "endpoint", GUID, sa.ForeignKey("endpoints.id", ondelete="SET NULL"), nullable=True
    )
    session_owner = ForeignKeyIDColumn("session_owner", "users.uuid")
    domain = sa.Column(
        "domain",
        sa.String(length=64),
        sa.ForeignKey("domains.name", ondelete="CASCADE"),
        nullable=False,
    )
    project = sa.Column(
        "project",
        GUID,
        sa.ForeignKey("groups.id", ondelete="CASCADE"),
        nullable=False,
    )
    created_at = sa.Column(
        "created_at", sa.DateTime(timezone=True), server_default=sa.text("now()"), nullable=True
    )

    endpoint_row = relationship("EndpointRow", back_populates="tokens")

    def __init__(
        self,
        id: uuid.UUID,
        token: str,
        endpoint: uuid.UUID,
        domain: str,
        project: uuid.UUID,
        session_owner: uuid.UUID,
    ) -> None:
        self.id = id
        self.token = token
        self.endpoint = endpoint
        self.domain = domain
        self.project = project
        self.session_owner = session_owner

    @classmethod
    async def list(
        cls,
        session: AsyncSession,
        endpoint_id: uuid.UUID,
        *,
        domain: Optional[str] = None,
        project: Optional[uuid.UUID] = None,
        user_uuid: Optional[uuid.UUID] = None,
        load_endpoint=False,
    ) -> Iterable["EndpointTokenRow"]:
        query = (
            sa.select(EndpointTokenRow)
            .filter(EndpointTokenRow.endpoint == endpoint_id)
            .order_by(sa.desc(EndpointTokenRow.created_at))
        )
        if load_endpoint:
            query = query.options(selectinload(EndpointTokenRow.tokens))
        if project:
            query = query.filter(EndpointTokenRow.project == project)
        if domain:
            query = query.filter(EndpointTokenRow.domain == domain)
        if user_uuid:
            query = query.filter(EndpointTokenRow.session_owner == user_uuid)
        result = await session.execute(query)
        return result.scalars().all()

    @classmethod
    async def get(
        cls,
        session: AsyncSession,
        token: str,
        *,
        domain: Optional[str] = None,
        project: Optional[uuid.UUID] = None,
        user_uuid: Optional[uuid.UUID] = None,
        load_endpoint=False,
    ) -> "EndpointTokenRow":
        query = sa.select(EndpointTokenRow).filter(EndpointTokenRow.token == token)
        if load_endpoint:
            query = query.options(selectinload(EndpointTokenRow.tokens))
        if project:
            query = query.filter(EndpointTokenRow.project == project)
        if domain:
            query = query.filter(EndpointTokenRow.domain == domain)
        if user_uuid:
            query = query.filter(EndpointTokenRow.session_owner == user_uuid)
        result = await session.execute(query)
        row = result.scalar()
        if not row:
            raise NoResultFound
        return row


class Endpoint(graphene.ObjectType):
    class Meta:
        interfaces = (Item,)

    endpoint_id = graphene.UUID()
    image = graphene.String(deprecation_reason="Deprecated since 23.09.9; use `image_object`")
    image_object = graphene.Field(ImageNode, description="Added at 23.09.9")
    domain = graphene.String()
    project = graphene.String()
    resource_group = graphene.String()
    resource_slots = graphene.JSONString()
    url = graphene.String()
    model = graphene.UUID()
    model_mount_destiation = graphene.String()
    created_user = graphene.UUID(
        deprecation_reason="Deprecated since 23.09.8; use `created_user_id`"
    )
    created_user_email = graphene.String(description="Added at 23.09.8")
    created_user_id = graphene.UUID(description="Added at 23.09.8")
    session_owner = graphene.UUID(
        deprecation_reason="Deprecated since 23.09.8; use `session_owner_id`"
    )
    session_owner_email = graphene.String(description="Added at 23.09.8")
    session_owner_id = graphene.UUID(description="Added at 23.09.8")
    tag = graphene.String()
    startup_command = graphene.String()
    bootstrap_script = graphene.String()
    callback_url = graphene.String()
    environ = graphene.JSONString()
    name = graphene.String()
    resource_opts = graphene.JSONString()
    desired_session_count = graphene.Int()
    cluster_mode = graphene.String()
    cluster_size = graphene.Int()
    open_to_public = graphene.Boolean()

    created_at = GQLDateTime(required=True)
    destroyed_at = GQLDateTime()

    routings = graphene.List(Routing)
    retries = graphene.Int()
    status = graphene.String()

    lifecycle_stage = graphene.String()

    errors = graphene.List(graphene.NonNull(InferenceSessionError), required=True)

    @classmethod
    async def from_row(
        cls,
        ctx,  # ctx: GraphQueryContext,
        row: EndpointRow,
    ) -> "Endpoint":
        return cls(
            endpoint_id=row.id,
            # image="", # deprecated, row.image_object.name,
            image_object=ImageNode.from_row(row.image_row),
            domain=row.domain,
            project=row.project,
            resource_group=row.resource_group,
            resource_slots=row.resource_slots.to_json(),
            url=row.url,
            model=row.model,
            model_mount_destiation=row.model_mount_destiation,
            created_user=row.created_user,
            created_user_id=row.created_user,
            created_user_email=row.created_user_row.email,
            session_owner=row.session_owner,
            session_owner_id=row.session_owner,
            session_owner_email=row.session_owner_row.email,
            tag=row.tag,
            startup_command=row.startup_command,
            bootstrap_script=row.bootstrap_script,
            callback_url=row.callback_url,
            environ=row.environ,
            name=row.name,
            resource_opts=row.resource_opts,
            desired_session_count=row.desired_session_count,
            cluster_mode=row.cluster_mode,
            cluster_size=row.cluster_size,
            open_to_public=row.open_to_public,
            created_at=row.created_at,
            destroyed_at=row.destroyed_at,
            retries=row.retries,
            routings=[await Routing.from_row(None, r, endpoint=row) for r in row.routings],
            lifecycle_stage=row.lifecycle_stage.name,
        )

    @classmethod
    async def load_count(
        cls,
        ctx,  # ctx: GraphQueryContext,
        *,
        project: uuid.UUID | None = None,
        domain_name: Optional[str] = None,
        user_uuid: Optional[uuid.UUID] = None,
    ) -> int:
        query = (
            sa.select([sa.func.count()])
            .select_from(EndpointRow)
            .filter(
                EndpointRow.lifecycle_stage.in_([
                    EndpointLifecycle.CREATED,
                    EndpointLifecycle.DESTROYING,
                ])
            )
        )
        if project is not None:
            query = query.where(EndpointRow.project == project)
        if domain_name is not None:
            query = query.where(EndpointRow.domain == domain_name)
        if user_uuid is not None:
            query = query.where(EndpointRow.session_owner == user_uuid)
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
        domain_name: Optional[str] = None,
        user_uuid: Optional[uuid.UUID] = None,
        project: Optional[uuid.UUID] = None,
        filter: Optional[str] = None,
        order: Optional[str] = None,
    ) -> Sequence["Endpoint"]:
        query = (
            sa.select(EndpointRow)
            .limit(limit)
            .offset(offset)
            .options(selectinload(EndpointRow.image_row))
            .options(selectinload(EndpointRow.routings))
            .options(selectinload(EndpointRow.created_user_row))
            .options(selectinload(EndpointRow.session_owner_row))
            .order_by(sa.desc(EndpointRow.created_at))
            .filter(
                EndpointRow.lifecycle_stage.in_([
                    EndpointLifecycle.CREATED,
                    EndpointLifecycle.DESTROYING,
                ])
            )
        )
        if project is not None:
            query = query.where(EndpointRow.project == project)
        if domain_name is not None:
            query = query.where(EndpointRow.domain == domain_name)
        if user_uuid is not None:
            query = query.where(EndpointRow.session_owner == user_uuid)
        """
        if filter is not None:
            parser = QueryFilterParser(cls._queryfilter_fieldspec)
            query = parser.append_filter(query, filter)
        if order is not None:
            parser = QueryOrderParser(cls._queryorder_colmap)
            query = parser.append_ordering(query, order)
        """
        async with ctx.db.begin_readonly_session() as session:
            result = await session.execute(query)
            return [await cls.from_row(ctx, row) for row in result.scalars().all()]

    @classmethod
    async def load_all(
        cls,
        ctx,  # ctx: GraphQueryContext,
        *,
        domain_name: Optional[str] = None,
        user_uuid: Optional[uuid.UUID] = None,
        project: Optional[uuid.UUID] = None,
    ) -> Sequence["Endpoint"]:
        async with ctx.db.begin_readonly_session() as session:
            rows = await EndpointRow.list(
                session,
                project=project,
                domain=domain_name,
                user_uuid=user_uuid,
                load_image=True,
                load_created_user=True,
                load_session_owner=True,
            )
            return [await Endpoint.from_row(ctx, row) for row in rows]

    @classmethod
    async def load_item(
        cls,
        ctx,  # ctx: GraphQueryContext,
        *,
        endpoint_id: uuid.UUID,
        domain_name: Optional[str] = None,
        user_uuid: Optional[uuid.UUID] = None,
        project: uuid.UUID | None = None,
    ) -> "Endpoint":
        """
        :raises: ai.backend.manager.api.exceptions.EndpointNotFound
        """
        try:
            async with ctx.db.begin_readonly_session() as session:
                row = await EndpointRow.get(
                    session,
                    endpoint_id=endpoint_id,
                    domain=domain_name,
                    user_uuid=user_uuid,
                    project=project,
                    load_image=True,
                    load_routes=True,
                    load_created_user=True,
                    load_session_owner=True,
                )
                return await Endpoint.from_row(ctx, row)
        except NoResultFound:
            raise EndpointNotFound

    async def resolve_status(self, info: graphene.ResolveInfo) -> str:
        if self.retries > SERVICE_MAX_RETRIES:
            return "UNHEALTHY"
        if self.lifecycle_stage == EndpointLifecycle.DESTROYING:
            return "DESTROYING"
        if len(self.routings) == 0:
            return "READY"
        if (spawned_service_count := len([r for r in self.routings])) > 0:
            healthy_service_count = len([
                r for r in self.routings if r.status == RouteStatus.HEALTHY.name
            ])
            if healthy_service_count == spawned_service_count:
                return "HEALTHY"
            unhealthy_service_count = len([
                r for r in self.routings if r.status == RouteStatus.UNHEALTHY.name
            ])
            if unhealthy_service_count > 0:
                return "DEGRADED"
        return "PROVISIONING"

    async def resolve_errors(self, info: graphene.ResolveInfo) -> Any:
        error_routes = [r for r in self.routings if r.status == RouteStatus.FAILED_TO_START.name]
        errors = []
        for route in error_routes:
            match route.error_data["type"]:
                case "session_cancelled":
                    session_id = route.error_data["session_id"]
                case _:
                    session_id = None
            errors.append(
                InferenceSessionError(
                    session_id=session_id,
                    errors=[
                        InferenceSessionError.InferenceSessionErrorInfo(
                            src=e["src"], name=e["name"], repr=e["repr"]
                        )
                        for e in route.error_data["errors"]
                    ],
                )
            )

        return errors


class EndpointList(graphene.ObjectType):
    class Meta:
        interfaces = (PaginatedList,)

    items = graphene.List(Endpoint, required=True)


class ModifyEndpointInput(graphene.InputObjectType):
    resource_slots = graphene.JSONString()
    resource_opts = graphene.JSONString()
    cluster_mode = graphene.String()
    cluster_size = graphene.Int()
    desired_session_count = graphene.Int()
    image = ImageRefType()
    name = graphene.String()
    resource_group = graphene.String()
    open_to_public = graphene.Boolean()


class ModifyEndpoint(graphene.Mutation):
    class Arguments:
        endpoint_id = graphene.UUID(required=True)
        props = ModifyEndpointInput(required=True)

    ok = graphene.Boolean()
    msg = graphene.String()
    endpoint = graphene.Field(lambda: Endpoint, required=False, description="Added at 23.09.8")

    @classmethod
    async def mutate(
        cls,
        root,
        info: graphene.ResolveInfo,
        endpoint_id: uuid.UUID,
        props: ModifyEndpointInput,
    ) -> "ModifyEndpoint":
        graph_ctx: GraphQueryContext = info.context
        data: dict[str, Any] = {}
        set_if_set(
            props,
            data,
            "resource_slots",
            clean_func=lambda v: ResourceSlot.from_user_input(v, None),
        )
        set_if_set(props, data, "resource_opts")
        set_if_set(props, data, "cluster_mode")
        set_if_set(props, data, "cluster_size")
        set_if_set(props, data, "desired_session_count")
        set_if_set(props, data, "image")
        set_if_set(props, data, "resource_group")
        image = data.pop("image", None)

        async with graph_ctx.db.begin_readonly_session() as db_session:
            match graph_ctx.user["role"]:
                case UserRole.SUPERADMIN:
                    pass
                case UserRole.ADMIN:
                    domain_name = graph_ctx.user["domain_name"]
                    stmt = (
                        sa.select(EndpointRow)
                        .where(EndpointRow.id == endpoint_id)
                        .where(EndpointRow.domain == domain_name)
                    )
                    endpoint_row = (await db_session.scalars(stmt)).first()
                    if endpoint_row is None:
                        raise EndpointNotFound
                case _:
                    user_id = graph_ctx.user["uuid"]
                    stmt = (
                        sa.select(EndpointRow)
                        .where(EndpointRow.id == endpoint_id)
                        .where(
                            (EndpointRow.session_owner == user_id)
                            | (EndpointRow.created_user == user_id)
                        )
                    )
                    endpoint_row = (await db_session.scalars(stmt)).first()
                    if endpoint_row is None:
                        raise EndpointNotFound

            if image is not None:
                image_name = image["name"]
                registry = image.get("registry") or ["*"]
                arch = image.get("architecture")
                if arch is not None:
                    image_ref = ImageRef(image_name, registry, arch)
                else:
                    image_ref = ImageRef(
                        image_name,
                        registry,
                    )
                image_object = await ImageRow.resolve(db_session, [image_ref])
                data["image"] = image_object.id

        update_query = sa.update(EndpointRow).values(**data).where(EndpointRow.id == endpoint_id)

        async def _post(conn, result) -> EndpointRow:
            endpoint = result.first()
            try:
                async with AsyncSession(conn) as session:
                    row = await EndpointRow.get(
                        session,
                        endpoint_id=endpoint.id,
                        domain=endpoint.domain,
                        user_uuid=endpoint.created_user,
                        project=endpoint.project,
                        load_image=True,
                        load_routes=True,
                        load_created_user=True,
                        load_session_owner=True,
                    )
                return row
            except NoResultFound:
                raise EndpointNotFound

        return await simple_db_mutate_returning_item(
            cls, graph_ctx, update_query, item_cls=Endpoint, post_func=_post
        )


class EndpointToken(graphene.ObjectType):
    class Meta:
        interfaces = (Item,)

    token = graphene.String(required=True)
    endpoint_id = graphene.UUID(required=True)
    domain = graphene.String(required=True)
    project = graphene.String(required=True)
    session_owner = graphene.UUID(required=True)

    created_at = GQLDateTime(required=True)
    valid_until = GQLDateTime()

    @classmethod
    async def from_row(
        cls,
        ctx,  # ctx: GraphQueryContext,
        row: EndpointTokenRow,
    ) -> "EndpointToken":
        return cls(
            token=row.token,
            endpoint_id=row.endpoint,
            domain=row.domain,
            project=row.project,
            session_owner=row.session_owner,
            created_at=row.created_at,
        )

    @classmethod
    async def load_count(
        cls,
        ctx,  # ctx: GraphQueryContext,
        *,
        endpoint_id: Optional[uuid.UUID] = None,
        project: Optional[uuid.UUID] = None,
        domain_name: Optional[str] = None,
        user_uuid: Optional[uuid.UUID] = None,
    ) -> int:
        query = sa.select([sa.func.count()]).select_from(EndpointTokenRow)
        if endpoint_id is not None:
            query = query.where(EndpointTokenRow.endpoint == endpoint_id)
        if project:
            query = query.filter(EndpointTokenRow.project == project)
        if domain_name:
            query = query.filter(EndpointTokenRow.domain == domain_name)
        if user_uuid:
            query = query.filter(EndpointTokenRow.session_owner == user_uuid)
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
        endpoint_id: Optional[uuid.UUID] = None,
        filter: str | None = None,
        order: str | None = None,
        project: Optional[uuid.UUID] = None,
        domain_name: Optional[str] = None,
        user_uuid: Optional[uuid.UUID] = None,
    ) -> Sequence["EndpointToken"]:
        query = (
            sa.select(EndpointTokenRow)
            .limit(limit)
            .offset(offset)
            .order_by(sa.desc(EndpointTokenRow.created_at))
        )
        if endpoint_id is not None:
            query = query.where(EndpointTokenRow.endpoint == endpoint_id)
        if project:
            query = query.filter(EndpointTokenRow.project == project)
        if domain_name:
            query = query.filter(EndpointTokenRow.domain == domain_name)
        if user_uuid:
            query = query.filter(EndpointTokenRow.session_owner == user_uuid)
        """
        if filter is not None:
            parser = QueryFilterParser(cls._queryfilter_fieldspec)
            query = parser.append_filter(query, filter)
        if order is not None:
            parser = QueryOrderParser(cls._queryorder_colmap)
            query = parser.append_ordering(query, order)
        """
        async with ctx.db.begin_readonly_session() as session:
            result = await session.execute(query)
            return [await cls.from_row(ctx, row) for row in result.scalars().all()]

    @classmethod
    async def load_all(
        cls,
        ctx,  # ctx: GraphQueryContext
        endpoint_id: uuid.UUID,
        *,
        project: Optional[uuid.UUID] = None,
        domain_name: Optional[str] = None,
        user_uuid: Optional[uuid.UUID] = None,
    ) -> Sequence["EndpointToken"]:
        async with ctx.db.begin_readonly_session() as session:
            rows = await EndpointTokenRow.list(
                session,
                endpoint_id,
                project=project,
                domain=domain_name,
                user_uuid=user_uuid,
            )
        return [await EndpointToken.from_row(ctx, row) for row in rows]

    @classmethod
    async def load_item(
        cls,
        ctx,  # ctx: GraphQueryContext,
        token: str,
        *,
        project: Optional[uuid.UUID] = None,
        domain_name: Optional[str] = None,
        user_uuid: Optional[uuid.UUID] = None,
    ) -> "EndpointToken":
        try:
            async with ctx.db.begin_readonly_session() as session:
                row = await EndpointTokenRow.get(
                    session, token, project=project, domain=domain_name, user_uuid=user_uuid
                )
        except NoResultFound:
            raise EndpointTokenNotFound
        return await EndpointToken.from_row(ctx, row)

    async def resolve_valid_until(
        self,
        info: graphene.ResolveInfo,
    ) -> datetime.datetime | None:
        try:
            decoded = jwt.decode(
                self.token,
                algorithms=["HS256"],
                options={"verify_signature": False, "verify_exp": False},
            )
        except jwt.DecodeError:
            return None
        if "exp" not in decoded:
            return None
        return datetime.datetime.fromtimestamp(decoded["exp"])


class EndpointTokenList(graphene.ObjectType):
    class Meta:
        interfaces = (PaginatedList,)

    items = graphene.List(EndpointToken, required=True)
