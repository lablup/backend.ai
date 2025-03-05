from __future__ import annotations

import logging
from collections.abc import MutableMapping, Sequence
from dataclasses import dataclass
from decimal import Decimal
from typing import (
    TYPE_CHECKING,
    Any,
    AsyncIterator,
    Iterable,
    List,
    Optional,
    Self,
    overload,
)
from uuid import UUID

import graphene
import graphql
import sqlalchemy as sa
from dateutil.parser import parse as dtparse
from graphql import Undefined
from redis.asyncio import Redis
from redis.asyncio.client import Pipeline
from sqlalchemy.orm import selectinload

from ai.backend.common import redis_helper
from ai.backend.common.container_registry import ContainerRegistryType
from ai.backend.common.docker import ImageRef
from ai.backend.common.dto.agent.response import PurgeImageResponses
from ai.backend.common.exception import UnknownImageReference
from ai.backend.common.types import (
    AgentId,
    DispatchResult,
    ImageAlias,
)
from ai.backend.logging import BraceStyleAdapter
from ai.backend.manager.models.container_registry import ContainerRegistryRow
from ai.backend.manager.models.minilang.ordering import ColumnMapType, QueryOrderParser
from ai.backend.manager.models.minilang.queryfilter import (
    FieldSpecType,
    QueryFilterParser,
    enum_field_getter,
)
from ai.backend.manager.models.rbac.context import ClientContext
from ai.backend.manager.models.rbac.permission_defs import ImagePermission

from ...api.exceptions import GenericForbidden, ImageNotFound, ObjectNotFound
from ...defs import DEFAULT_IMAGE_ARCH
from ..base import (
    FilterExprArg,
    OrderExprArg,
    batch_multiresult_in_scalar_stream,
    generate_sql_info_for_gql_connection,
    set_if_set,
)
from ..gql_relay import AsyncNode, Connection, ConnectionResolverResult, ResolvedGlobalID
from ..image import (
    ImageAliasRow,
    ImageIdentifier,
    ImageLoadFilter,
    ImageRow,
    ImageStatus,
    ImageType,
    get_permission_ctx,
    rescan_images,
)
from ..rbac import ScopeType
from ..user import UserRole
from .base import (
    BigInt,
    ImageRefType,
    KVPair,
    KVPairInput,
    ResourceLimit,
    ResourceLimitInput,
    extract_object_uuid,
)

if TYPE_CHECKING:
    from ai.backend.common.bgtask import ProgressReporter

    from ..gql import GraphQueryContext

log = BraceStyleAdapter(logging.getLogger(__spec__.name))

__all__ = (
    "Image",
    "ImageNode",
    "PreloadImage",
    "RescanImages",
    "ForgetImage",
    "ForgetImageById",
    "PurgeImageById",
    "UntagImageFromRegistry",
    "ModifyImage",
    "AliasImage",
    "DealiasImage",
    "ClearImages",
)

_queryfilter_fieldspec: FieldSpecType = {
    "id": ("id", None),
    "name": ("name", None),
    "project": ("project", None),
    "image": ("image", None),
    "created_at": ("created_at", dtparse),
    "registry": ("registry", None),
    "registry_id": ("registry_id", None),
    "architecture": ("architecture", None),
    "is_local": ("is_local", None),
    "type": ("session_type", enum_field_getter(ImageType)),
    "accelerators": ("accelerators", None),
}

_queryorder_colmap: ColumnMapType = {
    "id": ("id", None),
    "name": ("name", None),
    "project": ("project", None),
    "image": ("image", None),
    "created_at": ("created_at", None),
    "registry": ("registry", None),
    "registry_id": ("registry_id", None),
    "architecture": ("architecture", None),
    "is_local": ("is_local", None),
    "type": ("session_type", None),
    "accelerators": ("accelerators", None),
}

ImageStatusType = graphene.Enum.from_enum(ImageStatus, description="Added in 25.4.0.")


class Image(graphene.ObjectType):
    id = graphene.UUID()
    name = graphene.String(deprecation_reason="Deprecated since 24.12.0. use `namespace` instead")
    namespace = graphene.String(description="Added in 24.12.0.")
    base_image_name = graphene.String(description="Added in 24.12.0.")
    project = graphene.String(description="Added in 24.03.10.")
    humanized_name = graphene.String()
    tag = graphene.String()
    tags = graphene.List(KVPair, description="Added in 24.12.0.")
    version = graphene.String(description="Added in 24.12.0.")
    registry = graphene.String()
    architecture = graphene.String()
    is_local = graphene.Boolean()
    digest = graphene.String()
    labels = graphene.List(KVPair)
    aliases = graphene.List(graphene.String)
    size_bytes = BigInt()
    status = graphene.String(description="Added in 25.4.0.")
    resource_limits = graphene.List(ResourceLimit)
    supported_accelerators = graphene.List(graphene.String)
    installed = graphene.Boolean()
    installed_agents = graphene.List(graphene.String)
    # legacy field
    hash = graphene.String()

    # internal attributes
    raw_labels: dict[str, Any]

    @classmethod
    def populate_row(
        cls,
        ctx: GraphQueryContext,
        row: ImageRow,
        installed_agents: List[str],
    ) -> Image:
        is_superadmin = ctx.user["role"] == UserRole.SUPERADMIN
        hide_agents = False if is_superadmin else ctx.local_config["manager"]["hide-agents"]
        image_ref = row.image_ref
        version, ptag_set = image_ref.tag_set
        ret = cls(
            id=row.id,
            name=row.image,
            namespace=row.image,
            base_image_name=image_ref.name,
            project=row.project,
            humanized_name=row.image,
            tag=row.tag,
            tags=[KVPair(key=k, value=v) for k, v in ptag_set.items()],
            version=version,
            registry=row.registry,
            architecture=row.architecture,
            is_local=row.is_local,
            digest=row.trimmed_digest or None,
            labels=[KVPair(key=k, value=v) for k, v in row.labels.items()],
            aliases=[alias_row.alias for alias_row in row.aliases],
            size_bytes=row.size_bytes,
            status=row.status,
            resource_limits=[
                ResourceLimit(
                    key=k,
                    min=v.get("min", Decimal(0)),
                    max=v.get("max", Decimal("Infinity")),
                )
                for k, v in row.resources.items()
            ],
            supported_accelerators=(row.accelerators or "").split(","),
            installed=len(installed_agents) > 0,
            installed_agents=installed_agents if not hide_agents else None,
            # legacy
            hash=row.trimmed_digest or None,
        )
        ret.raw_labels = row.labels
        return ret

    @classmethod
    async def from_row(
        cls,
        ctx: GraphQueryContext,
        row: ImageRow,
    ) -> Image:
        # TODO: add architecture
        _installed_agents = await redis_helper.execute(
            ctx.redis_image,
            lambda r: r.smembers(row.name),
        )
        installed_agents: List[str] = []
        for agent_id in _installed_agents:
            if isinstance(agent_id, bytes):
                installed_agents.append(agent_id.decode())
            else:
                installed_agents.append(agent_id)
        return cls.populate_row(ctx, row, installed_agents)

    @classmethod
    async def bulk_load(
        cls,
        ctx: GraphQueryContext,
        rows: List[ImageRow],
    ) -> AsyncIterator[Image]:
        async def _pipe(r: Redis) -> Pipeline:
            pipe = r.pipeline()
            for row in rows:
                await pipe.smembers(row.name)
            return pipe

        results = await redis_helper.execute(ctx.redis_image, _pipe)
        for idx, row in enumerate(rows):
            installed_agents: List[str] = []
            _installed_agents = results[idx]
            for agent_id in _installed_agents:
                if isinstance(agent_id, bytes):
                    installed_agents.append(agent_id.decode())
                else:
                    installed_agents.append(agent_id)
            yield cls.populate_row(ctx, row, installed_agents)

    @classmethod
    async def batch_load_by_canonical(
        cls,
        graph_ctx: GraphQueryContext,
        image_names: Sequence[str],
        filter_by_statuses: Optional[list[ImageStatus]] = [ImageStatus.ALIVE],
    ) -> Sequence[Optional[Image]]:
        query = (
            sa.select(ImageRow)
            .where(ImageRow.name.in_(image_names))
            .options(selectinload(ImageRow.aliases))
        )
        if filter_by_statuses:
            query = query.where(ImageRow.status.in_(filter_by_statuses))
        async with graph_ctx.db.begin_readonly_session() as session:
            result = await session.execute(query)
            return [await Image.from_row(graph_ctx, row) for row in result.scalars().all()]

    @classmethod
    async def batch_load_by_image_ref(
        cls,
        graph_ctx: GraphQueryContext,
        image_refs: Sequence[ImageRef],
        filter_by_statuses: Optional[list[ImageStatus]] = [ImageStatus.ALIVE],
    ) -> Sequence[Optional[Image]]:
        image_names = [x.canonical for x in image_refs]
        return await cls.batch_load_by_canonical(graph_ctx, image_names, filter_by_statuses)

    @classmethod
    async def load_item_by_id(
        cls,
        ctx: GraphQueryContext,
        id: UUID,
        filter_by_statuses: Optional[list[ImageStatus]] = [ImageStatus.ALIVE],
    ) -> Image:
        async with ctx.db.begin_readonly_session() as session:
            row = await ImageRow.get(
                session, id, load_aliases=True, filter_by_statuses=filter_by_statuses
            )
            if not row:
                raise ImageNotFound

            return await cls.from_row(ctx, row)

    @classmethod
    async def load_item(
        cls,
        ctx: GraphQueryContext,
        reference: str,
        architecture: str,
        filter_by_statuses: Optional[list[ImageStatus]] = [ImageStatus.ALIVE],
    ) -> Image:
        try:
            async with ctx.db.begin_readonly_session() as session:
                image_row = await ImageRow.resolve(
                    session,
                    [
                        ImageIdentifier(reference, architecture),
                        ImageAlias(reference),
                    ],
                    filter_by_statuses=filter_by_statuses,
                )
        except UnknownImageReference:
            raise ImageNotFound
        return await cls.from_row(ctx, image_row)

    @classmethod
    async def load_all(
        cls,
        ctx: GraphQueryContext,
        *,
        types: set[ImageLoadFilter] = set(),
        filter_by_statuses: Optional[list[ImageStatus]] = [ImageStatus.ALIVE],
    ) -> Sequence[Image]:
        async with ctx.db.begin_readonly_session() as session:
            rows = await ImageRow.list(
                session, load_aliases=True, filter_by_statuses=filter_by_statuses
            )
        items: list[Image] = [
            item async for item in cls.bulk_load(ctx, rows) if item.matches_filter(ctx, types)
        ]

        return items

    @staticmethod
    async def filter_allowed(
        ctx: GraphQueryContext,
        items: Sequence[Image],
        domain_name: str,
    ) -> Sequence[Image]:
        from ..domain import domains

        async with ctx.db.begin() as conn:
            query = (
                sa.select([domains.c.allowed_docker_registries])
                .select_from(domains)
                .where(domains.c.name == domain_name)
            )
            result = await conn.execute(query)
            allowed_docker_registries = result.scalar()

        filtered_items: list[Image] = [
            item for item in items if item.registry in allowed_docker_registries
        ]

        return filtered_items

    def matches_filter(
        self,
        ctx: GraphQueryContext,
        load_filters: set[ImageLoadFilter],
    ) -> bool:
        """
        Determine if the image is filtered according to the `load_filters` parameter.
        """
        user_role = ctx.user["role"]

        # If the image filtered by any of its labels, return False early.
        # If the image is not filtered and is determiend to be valid by any of its labels, `is_valid = True`.
        is_valid = ImageLoadFilter.GENERAL in load_filters
        for label in self.labels:
            match label.key:
                case "ai.backend.features" if "operation" in label.value:
                    if ImageLoadFilter.OPERATIONAL in load_filters:
                        is_valid = True
                    else:
                        return False
                case "ai.backend.customized-image.owner":
                    if (
                        ImageLoadFilter.CUSTOMIZED not in load_filters
                        and ImageLoadFilter.CUSTOMIZED_GLOBAL not in load_filters
                    ):
                        return False
                    if ImageLoadFilter.CUSTOMIZED in load_filters:
                        if label.value == f"user:{ctx.user['uuid']}":
                            is_valid = True
                        else:
                            return False
                    if ImageLoadFilter.CUSTOMIZED_GLOBAL in load_filters:
                        if user_role == UserRole.SUPERADMIN:
                            is_valid = True
                        else:
                            return False
        return is_valid


class ImagePermissionValueField(graphene.Scalar):
    class Meta:
        description = f"Added in 25.3.0. One of {[val.value for val in ImagePermission]}."

    @staticmethod
    def serialize(val: ImagePermission) -> str:
        return val.value

    @staticmethod
    def parse_literal(node: Any, _variables=None):
        if isinstance(node, graphql.language.ast.StringValueNode):
            return ImagePermission(node.value)

    @staticmethod
    def parse_value(value: str) -> ImagePermission:
        return ImagePermission(value)


class ImageNode(graphene.ObjectType):
    class Meta:
        interfaces = (AsyncNode,)

    row_id = graphene.UUID(description="Added in 24.03.4. The undecoded id value stored in DB.")
    name = graphene.String(deprecation_reason="Deprecated since 24.12.0. use `namespace` instead")
    namespace = graphene.String(description="Added in 24.12.0.")
    base_image_name = graphene.String(description="Added in 24.12.0.")
    project = graphene.String(description="Added in 24.03.10.")
    humanized_name = graphene.String()
    tag = graphene.String()
    tags = graphene.List(KVPair, description="Added in 24.12.0.")
    version = graphene.String(description="Added in 24.12.0.")
    registry = graphene.String()
    architecture = graphene.String()
    is_local = graphene.Boolean()
    digest = graphene.String()
    labels = graphene.List(KVPair)
    size_bytes = BigInt()
    status = graphene.String(description="Added in 25.4.0.")
    resource_limits = graphene.List(ResourceLimit)
    supported_accelerators = graphene.List(graphene.String)
    aliases = graphene.List(
        graphene.String, description="Added in 24.03.4. The array of image aliases."
    )

    permissions = graphene.List(
        ImagePermissionValueField,
        description=f"Added in 25.3.0. One of {[val.value for val in ImagePermission]}.",
    )

    @classmethod
    async def batch_load_by_name_and_arch(
        cls,
        graph_ctx: GraphQueryContext,
        name_and_arch: Sequence[tuple[str, str]],
        filter_by_statuses: Optional[list[ImageStatus]] = [ImageStatus.ALIVE],
    ) -> Sequence[Sequence[ImageNode]]:
        query = (
            sa.select(ImageRow)
            .where(sa.tuple_(ImageRow.name, ImageRow.architecture).in_(name_and_arch))
            .options(selectinload(ImageRow.aliases))
        )
        if filter_by_statuses:
            query = query.where(ImageRow.status.in_(filter_by_statuses))

        async with graph_ctx.db.begin_readonly_session() as db_session:
            return await batch_multiresult_in_scalar_stream(
                graph_ctx,
                db_session,
                query,
                cls,
                name_and_arch,
                lambda row: (row.name, row.architecture),
            )

    @classmethod
    async def batch_load_by_image_identifier(
        cls,
        graph_ctx: GraphQueryContext,
        image_ids: Sequence[ImageIdentifier],
        filter_by_statuses: Optional[list[ImageStatus]] = [ImageStatus.ALIVE],
    ) -> Sequence[Sequence[ImageNode]]:
        name_and_arch_tuples = [(img.canonical, img.architecture) for img in image_ids]
        return await cls.batch_load_by_name_and_arch(
            graph_ctx, name_and_arch_tuples, filter_by_statuses
        )

    @overload
    @classmethod
    def from_row(cls, graph_ctx: GraphQueryContext, row: ImageRow) -> Self: ...

    @overload
    @classmethod
    def from_row(
        cls, graph_ctx, row: ImageRow, *, permissions: Optional[Iterable[ImagePermission]] = None
    ) -> ImageNode: ...

    @overload
    @classmethod
    def from_row(
        cls, graph_ctx, row: None, *, permissions: Optional[Iterable[ImagePermission]] = None
    ) -> None: ...

    @classmethod
    def from_row(
        cls,
        graph_ctx,
        row: Optional[ImageRow],
        *,
        permissions: Optional[Iterable[ImagePermission]] = None,
    ) -> ImageNode | None:
        if row is None:
            return None
        image_ref = row.image_ref
        version, ptag_set = image_ref.tag_set

        result = cls(
            id=row.id,
            row_id=row.id,
            name=row.image,
            namespace=row.image,
            base_image_name=image_ref.name,
            project=row.project,
            humanized_name=row.image,
            tag=row.tag,
            tags=[KVPair(key=k, value=v) for k, v in ptag_set.items()],
            version=version,
            registry=row.registry,
            architecture=row.architecture,
            is_local=row.is_local,
            digest=row.trimmed_digest or None,
            labels=[KVPair(key=k, value=v) for k, v in row.labels.items()],
            size_bytes=row.size_bytes,
            resource_limits=[
                ResourceLimit(
                    key=k,
                    min=v.get("min", Decimal(0)),
                    max=v.get("max", Decimal("Infinity")),
                )
                for k, v in row.resources.items()
            ],
            supported_accelerators=(row.accelerators or "").split(","),
            aliases=[alias_row.alias for alias_row in row.aliases],
            permissions=[] if permissions is None else permissions,
            status=row.status,
        )

        return result

    @classmethod
    def from_legacy_image(
        cls, row: Image, *, permissions: Optional[Iterable[ImagePermission]] = None
    ) -> ImageNode:
        result = cls(
            id=row.id,
            row_id=row.id,
            name=row.name,
            namespace=row.namespace,
            base_image_name=row.base_image_name,
            humanized_name=row.humanized_name,
            tag=row.tag,
            tags=row.tags,
            version=row.version,
            project=row.project,
            registry=row.registry,
            architecture=row.architecture,
            is_local=row.is_local,
            digest=row.digest,
            labels=row.labels,
            size_bytes=row.size_bytes,
            resource_limits=row.resource_limits,
            supported_accelerators=row.supported_accelerators,
            aliases=row.aliases,
            permissions=[] if permissions is None else permissions,
            status=row.status,
        )
        return result

    @classmethod
    async def get_node(
        cls,
        info: graphene.ResolveInfo,
        id: ResolvedGlobalID,
        scope_id: ScopeType,
        permission: ImagePermission = ImagePermission.READ_ATTRIBUTE,
    ) -> Optional[Self]:
        graph_ctx: GraphQueryContext = info.context

        _, image_id = id
        async with graph_ctx.db.connect() as db_conn:
            user = graph_ctx.user
            client_ctx = ClientContext(
                graph_ctx.db, user["domain_name"], user["uuid"], user["role"]
            )
            permission_ctx = await get_permission_ctx(db_conn, client_ctx, scope_id, permission)
            cond = permission_ctx.query_condition
            if cond is None:
                return None

            query = (
                sa.select(ImageRow)
                .where(cond & (ImageRow.id == UUID(image_id)))
                .options(selectinload(ImageRow.aliases))
            )

            async with graph_ctx.db.begin_readonly_session() as db_session:
                image_row = await db_session.scalar(query)
                if image_row is None:
                    return None

                return cls.from_row(
                    graph_ctx,
                    image_row,
                    permissions=await permission_ctx.calculate_final_permission(image_row),
                )

    @classmethod
    async def get_connection(
        cls,
        info: graphene.ResolveInfo,
        scope_id: ScopeType,
        permission: ImagePermission,
        filter_by_statuses: Optional[list[ImageStatus]] = [ImageStatus.ALIVE],
        filter_expr: Optional[str] = None,
        order_expr: Optional[str] = None,
        offset: Optional[int] = None,
        after: Optional[str] = None,
        first: Optional[int] = None,
        before: Optional[str] = None,
        last: Optional[int] = None,
    ) -> ConnectionResolverResult[Self]:
        graph_ctx: GraphQueryContext = info.context
        _filter_arg = (
            FilterExprArg(filter_expr, QueryFilterParser(_queryfilter_fieldspec))
            if filter_expr is not None
            else None
        )
        _order_expr = (
            OrderExprArg(order_expr, QueryOrderParser(_queryorder_colmap))
            if order_expr is not None
            else None
        )
        (
            query,
            cnt_query,
            _,
            cursor,
            pagination_order,
            page_size,
        ) = generate_sql_info_for_gql_connection(
            info,
            ImageRow,
            ImageRow.id,
            _filter_arg,
            _order_expr,
            offset,
            after=after,
            first=first,
            before=before,
            last=last,
        )
        async with graph_ctx.db.connect() as db_conn:
            user = graph_ctx.user
            client_ctx = ClientContext(
                graph_ctx.db, user["domain_name"], user["uuid"], user["role"]
            )
            permission_ctx = await get_permission_ctx(db_conn, client_ctx, scope_id, permission)
            cond = permission_ctx.query_condition
            if cond is None:
                return ConnectionResolverResult([], cursor, pagination_order, page_size, 0)
            query = query.where(cond).options(selectinload(ImageRow.aliases))
            cnt_query = cnt_query.where(cond)

            if filter_by_statuses:
                query = query.where(ImageRow.status.in_(filter_by_statuses))
                cnt_query = cnt_query.where(ImageRow.status.in_(filter_by_statuses))

            async with graph_ctx.db.begin_readonly_session(db_conn) as db_session:
                image_rows = (await db_session.scalars(query)).all()
                total_cnt = await db_session.scalar(cnt_query)
                result: list[Self] = [
                    cls.from_row(
                        graph_ctx,
                        row,
                        permissions=await permission_ctx.calculate_final_permission(row),
                    )
                    for row in image_rows
                ]
        return ConnectionResolverResult(result, cursor, pagination_order, page_size, total_cnt)


class ImageConnection(Connection):
    class Meta:
        node = ImageNode
        description = "Added in 25.3.0."


class ForgetImageById(graphene.Mutation):
    """Added in 24.03.0."""

    allowed_roles = (
        UserRole.SUPERADMIN,
        UserRole.ADMIN,
        UserRole.USER,
    )

    class Arguments:
        image_id = graphene.String(required=True)

    ok = graphene.Boolean()
    msg = graphene.String()
    image = graphene.Field(ImageNode, description="Added since 24.03.1.")

    @staticmethod
    async def mutate(
        root: Any,
        info: graphene.ResolveInfo,
        image_id: str,
    ) -> ForgetImageById:
        log.info("forget image {0} by API request", image_id)
        image_uuid = extract_object_uuid(info, image_id, "image")

        ctx: GraphQueryContext = info.context
        client_role = ctx.user["role"]

        async with ctx.db.begin_session() as session:
            image_row = await ImageRow.get(session, image_uuid, load_aliases=True)
            if not image_row:
                raise ObjectNotFound("image")
            if client_role != UserRole.SUPERADMIN:
                if not image_row.is_customized_by(ctx.user["uuid"]):
                    return ForgetImageById(ok=False, msg="Forbidden")
            await image_row.mark_as_deleted(session)
            return ForgetImageById(ok=True, msg="", image=ImageNode.from_row(ctx, image_row))


class ForgetImage(graphene.Mutation):
    """
    Deprecated since 25.4.0. Use `forget_image_by_id` instead.
    """

    allowed_roles = (
        UserRole.SUPERADMIN,
        UserRole.ADMIN,
        UserRole.USER,
    )

    class Arguments:
        reference = graphene.String(required=True)
        architecture = graphene.String(default_value=DEFAULT_IMAGE_ARCH)

    ok = graphene.Boolean()
    msg = graphene.String()
    image = graphene.Field(ImageNode, description="Added since 24.03.1.")

    @staticmethod
    async def mutate(
        root: Any,
        info: graphene.ResolveInfo,
        reference: str,
        architecture: str,
    ) -> ForgetImage:
        log.info("forget image {0} by API request", reference)
        ctx: GraphQueryContext = info.context
        client_role = ctx.user["role"]

        async with ctx.db.begin_session() as session:
            image_row = await ImageRow.resolve(
                session,
                [
                    ImageIdentifier(reference, architecture),
                    ImageAlias(reference),
                ],
            )
            if client_role != UserRole.SUPERADMIN:
                if not image_row.is_customized_by(ctx.user["uuid"]):
                    return ForgetImage(ok=False, msg="Forbidden")
            await image_row.mark_as_deleted(session)
            return ForgetImage(ok=True, msg="", image=ImageNode.from_row(ctx, image_row))


class PurgeImageById(graphene.Mutation):
    """Added in 25.4.0."""

    allowed_roles = (
        UserRole.SUPERADMIN,
        UserRole.ADMIN,
        UserRole.USER,
    )

    class Arguments:
        image_id = graphene.String(required=True)

    image = graphene.Field(ImageNode)

    @staticmethod
    async def mutate(
        root: Any,
        info: graphene.ResolveInfo,
        image_id: str,
    ) -> PurgeImageById:
        log.info("purge image {0} by API request", image_id)
        image_uuid = extract_object_uuid(info, image_id, "image")

        ctx: GraphQueryContext = info.context
        client_role = ctx.user["role"]

        async with ctx.db.begin_session() as session:
            image_row = await ImageRow.get(session, image_uuid, load_aliases=True)
            if not image_row:
                raise ObjectNotFound("image")
            if client_role != UserRole.SUPERADMIN:
                if not image_row.is_customized_by(ctx.user["uuid"]):
                    raise GenericForbidden("Image is not owned by your account.")
            await session.delete(image_row)
            return PurgeImageById(image=ImageNode.from_row(ctx, image_row))


class UntagImageFromRegistry(graphene.Mutation):
    """Added in 24.03.1"""

    allowed_roles = (
        UserRole.SUPERADMIN,
        UserRole.ADMIN,
        UserRole.USER,
    )

    class Arguments:
        image_id = graphene.String(required=True)

    ok = graphene.Boolean()
    msg = graphene.String()
    image = graphene.Field(ImageNode, description="Added since 24.03.1.")

    @staticmethod
    async def mutate(
        root: Any,
        info: graphene.ResolveInfo,
        image_id: str,
    ) -> UntagImageFromRegistry:
        from ai.backend.manager.container_registry.harbor import HarborRegistry_v2

        image_uuid = extract_object_uuid(info, image_id, "image")

        log.info("remove image from registry {0} by API request", str(image_uuid))
        ctx: GraphQueryContext = info.context
        client_role = ctx.user["role"]

        async with ctx.db.begin_readonly_session() as session:
            image_row = await ImageRow.get(session, image_uuid, load_aliases=True)
            if not image_row:
                raise ImageNotFound
            if client_role != UserRole.SUPERADMIN:
                if not image_row.is_customized_by(ctx.user["uuid"]):
                    return UntagImageFromRegistry(ok=False, msg="Forbidden")

            query = sa.select(ContainerRegistryRow).where(
                ContainerRegistryRow.registry_name == image_row.image_ref.registry
            )

            registry_info = (await session.execute(query)).scalar()

            if registry_info.type != ContainerRegistryType.HARBOR2:
                raise NotImplementedError("This feature is only supported for Harbor 2 registries")

        scanner = HarborRegistry_v2(ctx.db, image_row.image_ref.registry, registry_info)
        await scanner.untag(image_row.image_ref)

        return UntagImageFromRegistry(ok=True, msg="", image=ImageNode.from_row(ctx, image_row))


class PreloadImage(graphene.Mutation):
    allowed_roles = (UserRole.SUPERADMIN,)

    class Arguments:
        references = graphene.List(graphene.String, required=True)
        target_agents = graphene.List(graphene.String, required=True)

    ok = graphene.Boolean()
    msg = graphene.String()
    task_id = graphene.String()

    @staticmethod
    async def mutate(
        root: Any,
        info: graphene.ResolveInfo,
        references: Sequence[str],
        target_agents: Sequence[str],
    ) -> PreloadImage:
        return PreloadImage(ok=False, msg="Not implemented.", task_id=None)


class UnloadImage(graphene.Mutation):
    allowed_roles = (UserRole.SUPERADMIN,)

    class Arguments:
        references = graphene.List(graphene.String, required=True)
        target_agents = graphene.List(graphene.String, required=True)

    ok = graphene.Boolean()
    msg = graphene.String()
    task_id = graphene.String()

    @staticmethod
    async def mutate(
        root: Any,
        info: graphene.ResolveInfo,
        references: Sequence[str],
        target_agents: Sequence[str],
    ) -> UnloadImage:
        return UnloadImage(ok=False, msg="Not implemented.", task_id=None)


class RescanImages(graphene.Mutation):
    allowed_roles = (UserRole.ADMIN, UserRole.SUPERADMIN)

    class Arguments:
        registry = graphene.String()
        project = graphene.String(description="Added in 25.1.0.")

    ok = graphene.Boolean()
    msg = graphene.String()
    task_id = graphene.UUID()

    @staticmethod
    async def mutate(
        root: Any,
        info: graphene.ResolveInfo,
        registry: Optional[str] = None,
        project: Optional[str] = None,
    ) -> RescanImages:
        log.info(
            "rescanning docker registry {0} by API request",
            f"(registry: {registry or 'all'}, project: {project or 'all'})",
        )
        ctx: GraphQueryContext = info.context

        async def _rescan_task(reporter: ProgressReporter) -> DispatchResult:
            return await rescan_images(ctx.db, registry, project, reporter=reporter)

        task_id = await ctx.background_task_manager.start(_rescan_task)
        return RescanImages(ok=True, msg="", task_id=task_id)


class AliasImage(graphene.Mutation):
    allowed_roles = (UserRole.SUPERADMIN,)

    class Arguments:
        alias = graphene.String(required=True)
        target = graphene.String(required=True)
        architecture = graphene.String(default_value=DEFAULT_IMAGE_ARCH)

    ok = graphene.Boolean()
    msg = graphene.String()

    @staticmethod
    async def mutate(
        root: Any,
        info: graphene.ResolveInfo,
        alias: str,
        target: str,
        architecture: str,
    ) -> AliasImage:
        log.info("alias image {0} -> {1} by API request", alias, target)
        ctx: GraphQueryContext = info.context
        try:
            async with ctx.db.begin_session() as session:
                try:
                    image_row = await ImageRow.resolve(
                        session, [ImageIdentifier(target, architecture)]
                    )
                except UnknownImageReference:
                    raise ImageNotFound
                else:
                    image_row.aliases.append(ImageAliasRow(alias=alias, image_id=image_row.id))
        except ValueError as e:
            return AliasImage(ok=False, msg=str(e))
        return AliasImage(ok=True, msg="")


class DealiasImage(graphene.Mutation):
    allowed_roles = (UserRole.SUPERADMIN,)

    class Arguments:
        alias = graphene.String(required=True)

    ok = graphene.Boolean()
    msg = graphene.String()

    @staticmethod
    async def mutate(
        root: Any,
        info: graphene.ResolveInfo,
        alias: str,
    ) -> DealiasImage:
        log.info("dealias image {0} by API request", alias)
        ctx: GraphQueryContext = info.context
        try:
            async with ctx.db.begin_session() as session:
                existing_alias = await session.scalar(
                    sa.select(ImageAliasRow).where(ImageAliasRow.alias == alias),
                )
                if existing_alias is None:
                    raise DealiasImage(ok=False, msg=str("No such alias"))
                await session.delete(existing_alias)
        except ValueError as e:
            return DealiasImage(ok=False, msg=str(e))
        return DealiasImage(ok=True, msg="")


class ClearImages(graphene.Mutation):
    allowed_roles = (UserRole.SUPERADMIN,)

    class Arguments:
        registry = graphene.String()

    ok = graphene.Boolean()
    msg = graphene.String()

    @staticmethod
    async def mutate(
        root: Any,
        info: graphene.ResolveInfo,
        registry: str,
    ) -> ClearImages:
        ctx: GraphQueryContext = info.context
        try:
            async with ctx.db.begin_session() as session:
                await session.execute(
                    sa.update(ImageRow)
                    .where(ImageRow.registry == registry)
                    .where(ImageRow.status != ImageStatus.DELETED)
                    .values(status=ImageStatus.DELETED)
                )
        except ValueError as e:
            return ClearImages(ok=False, msg=str(e))
        return ClearImages(ok=True, msg="")


class ModifyImageInput(graphene.InputObjectType):
    name = graphene.String(required=False)
    registry = graphene.String(required=False)
    image = graphene.String(required=False)
    tag = graphene.String(required=False)
    architecture = graphene.String(required=False)
    is_local = graphene.Boolean(required=False)
    size_bytes = graphene.Int(required=False)
    type = graphene.String(required=False)

    digest = graphene.String(required=False)
    labels = graphene.List(lambda: KVPairInput, required=False)
    supported_accelerators = graphene.List(graphene.String, required=False)
    resource_limits = graphene.List(lambda: ResourceLimitInput, required=False)


class ModifyImage(graphene.Mutation):
    allowed_roles = (UserRole.SUPERADMIN,)

    class Arguments:
        target = graphene.String(required=True, default_value=None)
        architecture = graphene.String(required=False, default_value=DEFAULT_IMAGE_ARCH)
        props = ModifyImageInput(required=True)

    ok = graphene.Boolean()
    msg = graphene.String()

    @staticmethod
    async def mutate(
        root: Any,
        info: graphene.ResolveInfo,
        target: str,
        architecture: str,
        props: ModifyImageInput,
    ) -> AliasImage:
        ctx: GraphQueryContext = info.context
        data: MutableMapping[str, Any] = {}
        set_if_set(props, data, "name")
        set_if_set(props, data, "registry")
        set_if_set(props, data, "image")
        set_if_set(props, data, "tag")
        set_if_set(props, data, "architecture")
        set_if_set(props, data, "is_local")
        set_if_set(props, data, "size_bytes")
        set_if_set(props, data, "type")
        set_if_set(props, data, "digest", target_key="config_digest")
        set_if_set(
            props,
            data,
            "supported_accelerators",
            clean_func=lambda v: ",".join(v),
            target_key="accelerators",
        )
        set_if_set(props, data, "labels", clean_func=lambda v: {pair.key: pair.value for pair in v})

        if props.resource_limits is not Undefined:
            resources_data = {}
            for limit_option in props.resource_limits:
                limit_data = {}
                if limit_option.min is not Undefined and len(limit_option.min) > 0:
                    limit_data["min"] = limit_option.min
                if limit_option.max is not Undefined and len(limit_option.max) > 0:
                    limit_data["max"] = limit_option.max
                resources_data[limit_option.key] = limit_data
            data["resources"] = resources_data

        try:
            async with ctx.db.begin_session() as session:
                try:
                    image_row = await ImageRow.resolve(
                        session,
                        [
                            ImageIdentifier(target, architecture),
                            ImageAlias(target),
                        ],
                    )
                except UnknownImageReference:
                    return ModifyImage(ok=False, msg="Image not found")
                for k, v in data.items():
                    setattr(image_row, k, v)
        except ValueError as e:
            return ModifyImage(ok=False, msg=str(e))
        return ModifyImage(ok=True, msg="")


@dataclass
class PurgeImagesResult:
    results: PurgeImageResponses
    reserved_bytes: int

    def __str__(self) -> str:
        results_str = "\n  ".join(
            f"{r.image}: {'Success' if not r.error else f'Failed (error: {r.error})'}"
            for r in self.results.responses
        )
        return f"PurgeImagesResult:\n  Reserved Bytes: {self.reserved_bytes}\n  Results:\n  {results_str}"


class PurgeImages(graphene.Mutation):
    """
    Added in 25.4.0.
    """

    allowed_roles = (UserRole.SUPERADMIN,)

    class Arguments:
        agent_id = graphene.String(required=True)
        images = graphene.List(ImageRefType, required=True)

    task_id = graphene.String()

    @staticmethod
    async def mutate(
        root: Any, info: graphene.ResolveInfo, agent_id: str, images: list[ImageRefType]
    ) -> PurgeImages:
        image_canonicals = [image.name for image in images]
        log.info(
            f"purge images ({image_canonicals}) from agent {agent_id} by API request",
        )
        ctx: GraphQueryContext = info.context

        async def _purge_images_task(
            reporter: ProgressReporter,
        ) -> DispatchResult[PurgeImagesResult]:
            errors = []
            task_result = PurgeImagesResult(results=PurgeImageResponses([]), reserved_bytes=0)
            arch_per_images = {image.name: image.architecture for image in images}

            results = await ctx.registry.purge_images(AgentId(agent_id), image_canonicals)

            for result in results.responses:
                image_canonical = result.image
                arch = arch_per_images[result.image]

                if not result.error:
                    image_identifier = ImageIdentifier(image_canonical, arch)
                    async with ctx.db.begin_session() as session:
                        image_row = await ImageRow.resolve(session, [image_identifier])
                        task_result.reserved_bytes += image_row.size_bytes
                        task_result.results.responses.append(result)

                else:
                    error_msg = f"Failed to purge image {image_canonical} from agent {agent_id}: {result.error}"
                    log.error(error_msg)
                    errors.append(error_msg)

            return DispatchResult(
                result=task_result,
                errors=errors,
            )

        task_id = await ctx.background_task_manager.start(_purge_images_task)
        return RescanImages(task_id=task_id)
