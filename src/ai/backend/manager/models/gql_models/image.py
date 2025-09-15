from __future__ import annotations

import logging
from collections.abc import Sequence
from decimal import Decimal
from typing import (
    TYPE_CHECKING,
    Any,
    AsyncIterator,
    Iterable,
    List,
    Optional,
    Self,
    cast,
    overload,
)
from uuid import UUID

import graphene
import graphene_federation
import graphql
import sqlalchemy as sa
from dateutil.parser import parse as dtparse
from graphql import Undefined, UndefinedType
from sqlalchemy.orm import selectinload

from ai.backend.common.bgtask.bgtask import ProgressReporter
from ai.backend.common.docker import ImageRef, KernelFeatures, LabelName
from ai.backend.common.exception import UnknownImageReference
from ai.backend.common.types import (
    AgentId,
    DispatchResult,
    ImageAlias,
)
from ai.backend.logging import BraceStyleAdapter
from ai.backend.manager.data.container_registry.types import ContainerRegistryData
from ai.backend.manager.models.minilang import EnumFieldItem
from ai.backend.manager.models.minilang.ordering import ColumnMapType, QueryOrderParser
from ai.backend.manager.models.minilang.queryfilter import (
    FieldSpecType,
    QueryFilterParser,
)
from ai.backend.manager.models.rbac.context import ClientContext
from ai.backend.manager.models.rbac.permission_defs import ImagePermission
from ai.backend.manager.services.container_registry.actions.clear_images import ClearImagesAction
from ai.backend.manager.services.container_registry.actions.load_all_container_registries import (
    LoadAllContainerRegistriesAction,
)
from ai.backend.manager.services.container_registry.actions.load_container_registries import (
    LoadContainerRegistriesAction,
)
from ai.backend.manager.services.container_registry.actions.rescan_images import RescanImagesAction
from ai.backend.manager.services.image.actions.alias_image import AliasImageAction
from ai.backend.manager.services.image.actions.clear_image_custom_resource_limit import (
    ClearImageCustomResourceLimitAction,
)
from ai.backend.manager.services.image.actions.dealias_image import DealiasImageAction
from ai.backend.manager.services.image.actions.forget_image import (
    ForgetImageAction,
)
from ai.backend.manager.services.image.actions.forget_image_by_id import ForgetImageByIdAction
from ai.backend.manager.services.image.actions.modify_image import (
    ImageModifier,
    ModifyImageAction,
)
from ai.backend.manager.services.image.actions.purge_image_by_id import PurgeImageByIdAction
from ai.backend.manager.services.image.actions.purge_images import (
    PurgedImagesData,
    PurgeImageAction,
    PurgeImageActionResult,
    PurgeImagesActionResult,
)
from ai.backend.manager.services.image.actions.untag_image_from_registry import (
    UntagImageFromRegistryAction,
)
from ai.backend.manager.services.image.types import ImageRefData
from ai.backend.manager.types import OptionalState, TriState

from ...data.image.types import ImageStatus, ImageType
from ...defs import DEFAULT_IMAGE_ARCH
from ...errors.image import ImageNotFound
from ..base import (
    FilterExprArg,
    OrderExprArg,
    batch_multiresult_in_scalar_stream,
    generate_sql_info_for_gql_connection,
)
from ..gql_relay import AsyncNode, Connection, ConnectionResolverResult, ResolvedGlobalID
from ..image import (
    ImageIdentifier,
    ImageLoadFilter,
    ImageRow,
    get_permission_ctx,
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
    "namespace": ("image", None),
    "tag": ("tag", None),
    "status": (EnumFieldItem("status", ImageStatus), None),
    "project": ("project", None),
    "image": ("image", None),
    "base_image_name": ("image", None),
    "created_at": ("created_at", dtparse),
    "registry": ("registry", None),
    "registry_id": ("registry_id", None),
    "architecture": ("architecture", None),
    "is_local": ("is_local", None),
    "type": (EnumFieldItem("type", ImageType), None),
    "accelerators": ("accelerators", None),
}

_queryorder_colmap: ColumnMapType = {
    "id": ("id", None),
    "name": ("name", None),
    "namespace": ("image", None),
    "tag": ("tag", None),
    "status": ("status", None),
    "project": ("project", None),
    "image": ("image", None),
    "base_image_name": ("image", None),
    "created_at": ("created_at", None),
    "registry": ("registry", None),
    "registry_id": ("registry_id", None),
    "architecture": ("architecture", None),
    "is_local": ("is_local", None),
    "type": ("session_type", None),
    "accelerators": ("accelerators", None),
}

ImageStatusType = graphene.Enum.from_enum(ImageStatus, description="Added in 25.4.0.")
ImageTypeEnum = graphene.Enum.from_enum(ImageType, description="Added in 25.12.0.")


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
        hide_agents = False if is_superadmin else ctx.config_provider.config.manager.hide_agents
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
                ResourceLimit(key=k, min=v.get("min", Decimal(0)), max=Decimal("Infinity"))
                for k, v in row.resources.items()
            ],
            supported_accelerators=row.accelerators.split(",") if row.accelerators else ["*"],
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
        _installed_agents = await ctx.valkey_image.get_agents_for_image(row.name)
        installed_agents: List[str] = list(_installed_agents)
        return cls.populate_row(ctx, row, installed_agents)

    @classmethod
    async def bulk_load(
        cls,
        ctx: GraphQueryContext,
        rows: List[ImageRow],
    ) -> AsyncIterator[Image]:
        image_canonicals = [row.name for row in rows]
        results = await ctx.valkey_image.get_agents_for_images(image_canonicals)

        for idx, row in enumerate(rows):
            installed_agents: List[str] = list(results[idx])
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
                case LabelName.FEATURES if KernelFeatures.OPERATION.value in label.value:
                    if ImageLoadFilter.OPERATIONAL in load_filters:
                        is_valid = True
                    else:
                        return False
                case LabelName.CUSTOMIZED_OWNER:
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


@graphene_federation.key("id")
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
    installed = graphene.Boolean(
        description="Added in 25.11.0. Indicates if the image is installed on any Agent."
    )
    type = ImageTypeEnum(description="Added in 25.12.0.")

    @property
    def _canonical(self) -> str:
        image_ref = ImageRef(
            self.base_image_name,
            self.project,
            self.tag,
            self.registry,
            self.architecture,
            self.is_local,
        )
        return image_ref.canonical

    @classmethod
    async def _batch_load_installed_agents(
        cls, ctx: GraphQueryContext, full_names: Sequence[str]
    ) -> list[set[AgentId]]:
        results = await ctx.valkey_image.get_agents_for_images(list(full_names))
        return [{AgentId(agent_id) for agent_id in agents} for agents in results]

    async def resolve_installed(self, info: graphene.ResolveInfo) -> bool:
        graph_ctx: GraphQueryContext = info.context
        loader = graph_ctx.dataloader_manager.get_loader_by_func(
            graph_ctx, self._batch_load_installed_agents
        )
        agent_ids = await loader.load(self._canonical)
        agent_ids = cast(Optional[set[AgentId]], agent_ids)
        return agent_ids is not None and len(agent_ids) > 0

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
        image_type = row.labels.get(LabelName.ROLE, ImageType.COMPUTE.value)

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
                ResourceLimit(key=k, min=v.get("min", Decimal(0)), max=Decimal("Infinity"))
                for k, v in row.resources.items()
            ],
            supported_accelerators=row.accelerators.split(",") if row.accelerators else ["*"],
            aliases=[alias_row.alias for alias_row in row.aliases],
            permissions=[] if permissions is None else permissions,
            status=row.status,
            type=image_type,
        )

        return result

    @classmethod
    def from_legacy_image(
        cls, image: Image, *, permissions: Optional[Iterable[ImagePermission]] = None
    ) -> ImageNode:
        labels: dict[str, str] = {kvpair.key: kvpair.value for kvpair in cast(list, image.labels)}
        image_type = labels.get(LabelName.ROLE, ImageType.COMPUTE.value)
        result = cls(
            id=image.id,
            row_id=image.id,
            name=image.name,
            namespace=image.namespace,
            base_image_name=image.base_image_name,
            humanized_name=image.humanized_name,
            tag=image.tag,
            tags=image.tags,
            version=image.version,
            project=image.project,
            registry=image.registry,
            architecture=image.architecture,
            is_local=image.is_local,
            digest=image.digest,
            labels=image.labels,
            size_bytes=image.size_bytes,
            resource_limits=image.resource_limits,
            supported_accelerators=image.supported_accelerators,
            aliases=image.aliases,
            permissions=[] if permissions is None else permissions,
            status=image.status,
            type=image_type,
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

        result = await ctx.processors.image.forget_image_by_id.wait_for_complete(
            ForgetImageByIdAction(
                user_id=ctx.user["uuid"],
                client_role=ctx.user["role"],
                image_id=image_uuid,
            )
        )

        return ForgetImageById(
            ok=True, msg="", image=ImageNode.from_row(ctx, ImageRow.from_dataclass(result.image))
        )


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

        result = await ctx.processors.image.forget_image.wait_for_complete(
            ForgetImageAction(
                user_id=ctx.user["uuid"],
                client_role=ctx.user["role"],
                reference=reference,
                architecture=architecture,
            )
        )

        return ForgetImage(
            ok=True, msg="", image=ImageNode.from_row(ctx, ImageRow.from_dataclass(result.image))
        )


class PurgeImageOptions(graphene.InputObjectType):
    """
    Added in 25.10.0.
    """

    remove_from_registry = graphene.Boolean(
        default_value=False,
        description="Untag the deleted image from the registry. Only available in the HarborV2 registry.",
    )


class PurgeImageById(graphene.Mutation):
    """Added in 25.4.0."""

    allowed_roles = (
        UserRole.SUPERADMIN,
        UserRole.ADMIN,
        UserRole.USER,
    )

    class Arguments:
        image_id = graphene.String(required=True)
        options = PurgeImageOptions(
            required=False,
            default_value={"remove_from_registry": False},
            description="Added in 25.10.0.",
        )

    image = graphene.Field(ImageNode)

    @staticmethod
    async def mutate(
        root: Any,
        info: graphene.ResolveInfo,
        image_id: str,
        options: PurgeImageOptions,
    ) -> PurgeImageById:
        log.info("purge image row {0} by API request", image_id)
        image_uuid = extract_object_uuid(info, image_id, "image")

        ctx: GraphQueryContext = info.context
        result = await ctx.processors.image.purge_image_by_id.wait_for_complete(
            PurgeImageByIdAction(
                user_id=ctx.user["uuid"],
                client_role=ctx.user["role"],
                image_id=image_uuid,
            )
        )

        if options.remove_from_registry:
            await ctx.processors.image.untag_image_from_registry.wait_for_complete(
                UntagImageFromRegistryAction(
                    user_id=ctx.user["uuid"],
                    client_role=ctx.user["role"],
                    image_id=image_uuid,
                )
            )

        return PurgeImageById(image=ImageNode.from_row(ctx, ImageRow.from_dataclass(result.image)))


class UntagImageFromRegistry(graphene.Mutation):
    """Deprecated since 25.10.0. Use `purge_image_by_id` with `remove_from_registry` option instead."""

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
        image_uuid = extract_object_uuid(info, image_id, "image")

        log.info("remove image from registry {0} by API request", str(image_uuid))
        ctx: GraphQueryContext = info.context
        result = await ctx.processors.image.untag_image_from_registry.wait_for_complete(
            UntagImageFromRegistryAction(
                user_id=ctx.user["uuid"],
                client_role=ctx.user["role"],
                image_id=image_uuid,
            )
        )

        return UntagImageFromRegistry(
            ok=True, msg="", image=ImageNode.from_row(ctx, ImageRow.from_dataclass(result.image))
        )


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

        async def _bg_task(reporter: ProgressReporter) -> DispatchResult:
            loaded_registries: list[ContainerRegistryData]

            if registry is None:
                all_registries = await ctx.processors.container_registry.load_all_container_registries.wait_for_complete(
                    LoadAllContainerRegistriesAction()
                )
                loaded_registries = all_registries.registries
            else:
                registries = await ctx.processors.container_registry.load_container_registries.wait_for_complete(
                    LoadContainerRegistriesAction(
                        registry=registry,
                        project=project,
                    )
                )
                loaded_registries = registries.registries

            rescanned_images = []
            errors = []
            for registry_data in loaded_registries:
                action_result = (
                    await ctx.processors.container_registry.rescan_images.wait_for_complete(
                        RescanImagesAction(
                            registry=registry_data.registry_name,
                            project=registry_data.project,
                            progress_reporter=reporter,
                        )
                    )
                )

                for error in action_result.errors:
                    log.error(error)

                errors.extend(action_result.errors)
                rescanned_images.extend(action_result.images)

            rescanned_image_ids = [image.id for image in rescanned_images]
            if errors:
                return DispatchResult.partial_success(rescanned_image_ids, errors)
            return DispatchResult.success(rescanned_image_ids)

        task_id = await ctx.background_task_manager.start(_bg_task)
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

        await ctx.processors.image.alias_image.wait_for_complete(
            AliasImageAction(
                image_canonical=target,
                architecture=architecture,
                alias=alias,
            )
        )

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

        await ctx.processors.image.dealias_image.wait_for_complete(
            DealiasImageAction(
                alias=alias,
            )
        )

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
        log.info("clear images from registry {0} by API request", registry)

        result = (
            await ctx.processors.container_registry.load_container_registries.wait_for_complete(
                LoadContainerRegistriesAction(
                    registry=registry,
                    project=None,
                )
            )
        )

        for registry_data in result.registries:
            await ctx.processors.container_registry.clear_images.wait_for_complete(
                ClearImagesAction(
                    registry=registry_data.registry_name,
                    project=registry_data.project,
                )
            )

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

    def to_modifier(self) -> ImageModifier:
        resources_data: dict[str, Any] | UndefinedType = Undefined
        if self.resource_limits is not Undefined:
            resources_data = {}
            for limit_option in self.resource_limits:
                limit_data = {}
                if limit_option.min is not Undefined and len(limit_option.min) > 0:
                    limit_data["min"] = limit_option.min
                if limit_option.max is not Undefined and len(limit_option.max) > 0:
                    limit_data["max"] = limit_option.max
                resources_data[limit_option.key] = limit_data

        accelerators = (
            ",".join(self.supported_accelerators) if self.supported_accelerators else Undefined
        )
        labels = {label.key: label.value for label in self.labels} if self.labels else Undefined

        return ImageModifier(
            name=OptionalState[str].from_graphql(self.name),
            registry=OptionalState[str].from_graphql(self.registry),
            image=OptionalState[str].from_graphql(self.image),
            tag=OptionalState[str].from_graphql(self.tag),
            architecture=OptionalState[str].from_graphql(self.architecture),
            is_local=OptionalState[bool].from_graphql(self.is_local),
            size_bytes=OptionalState[int].from_graphql(self.size_bytes),
            type=OptionalState[ImageType].from_graphql(self.type),
            config_digest=OptionalState[str].from_graphql(self.digest),
            labels=OptionalState[dict[str, Any]].from_graphql(labels),
            accelerators=TriState[str].from_graphql(
                accelerators,
            ),
            resources=OptionalState[dict[str, Any]].from_graphql(
                resources_data,
            ),
        )


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
        log.info("modify image {0} by API request", target)

        await ctx.processors.image.modify_image.wait_for_complete(
            ModifyImageAction(
                target=target,
                architecture=architecture,
                modifier=props.to_modifier(),
            )
        )

        return ModifyImage(ok=True, msg="")


class PurgeImagesKey(graphene.InputObjectType):
    """
    Added in 25.6.0.
    """

    agent_id = graphene.String(required=True)
    images = graphene.List(ImageRefType, required=True)


class PurgeImagesOptions(graphene.InputObjectType):
    """
    Added in 25.6.0.
    """

    force = graphene.Boolean(
        default_value=False,
        description="Remove the images even if it is being used by stopped containers or has other tags, Added in 25.6.0.",
    )
    noprune = graphene.Boolean(
        default_value=False, description="Don't delete untagged parent images, Added in 25.6.0."
    )


class PurgeImagesPayload(graphene.ObjectType):
    """
    Added in 25.6.0.
    """

    task_id = graphene.String()
    allowed_roles = (UserRole.SUPERADMIN, UserRole.ADMIN)


class PurgeImages(graphene.Mutation):
    """
    Added in 25.4.0.
    """

    class Arguments:
        keys = graphene.List(PurgeImagesKey, required=True)
        options = PurgeImagesOptions(default_value={"force": False, "noprune": False})

    Output = PurgeImagesPayload

    @staticmethod
    async def mutate(
        root: Any,
        info: graphene.ResolveInfo,
        keys: list[PurgeImagesKey],
        options: PurgeImagesOptions,
    ) -> PurgeImagesPayload:
        ctx: GraphQueryContext = info.context
        agent_images = ", ".join(
            f"{key.agent_id}: [{', '.join(img.name for img in key.images)}]" for key in keys
        )

        log.info(f"purge images ({agent_images}) by API request")

        async def _bg_task(reporter: ProgressReporter) -> DispatchResult:
            total_result: PurgeImagesActionResult = PurgeImagesActionResult(
                total_reserved_bytes=0,
                purged_images=[],
                errors=[],
            )

            for key in keys:
                agent_id = key.agent_id
                for img in key.images:
                    # TODO: Use asyncio.gather?
                    result: PurgeImageActionResult = (
                        await ctx.processors.image.purge_image.wait_for_complete(
                            PurgeImageAction(
                                ImageRefData(
                                    name=img.name,
                                    registry=img.registry,
                                    architecture=img.architecture,
                                ),
                                agent_id=agent_id,
                                force=options.force,
                                noprune=options.noprune,
                            )
                        )
                    )

                    total_result.total_reserved_bytes += result.reserved_bytes
                    total_result.purged_images.append(
                        PurgedImagesData(
                            agent_id=agent_id,
                            purged_images=[result.purged_image.name],
                        )
                    )

                    if result.error is not None:
                        log.error(result.error)
                        total_result.errors.append(result.error)

            if total_result.errors:
                return DispatchResult.partial_success(
                    total_result.purged_images, total_result.errors
                )
            return DispatchResult.success(total_result.purged_images)

        task_id = await ctx.background_task_manager.start(_bg_task)
        return PurgeImagesPayload(task_id=task_id)


class ClearImageCustomResourceLimitKey(graphene.InputObjectType):
    """
    Added in 25.6.0.
    """

    image_canonical = graphene.String(required=True)
    architecture = graphene.String(required=True, default_value=DEFAULT_IMAGE_ARCH)


class ClearImageCustomResourceLimitPayload(graphene.ObjectType):
    """
    Added in 25.6.0.
    """

    image_node = graphene.Field(ImageNode)
    allowed_roles = (UserRole.SUPERADMIN,)


class ClearImageCustomResourceLimit(graphene.Mutation):
    """
    Added in 25.6.0.
    """

    class Arguments:
        key = ClearImageCustomResourceLimitKey(required=True)

    Output = ClearImageCustomResourceLimitPayload

    @staticmethod
    async def mutate(
        root: Any,
        info: graphene.ResolveInfo,
        key: ClearImageCustomResourceLimitKey,
    ) -> ClearImageCustomResourceLimitPayload:
        log.info(
            f'clear custom resource limits for image "{key.image_canonical}" ({key.architecture}) by API request',
        )
        ctx: GraphQueryContext = info.context
        result = await ctx.processors.image.clear_image_custom_resource_limit.wait_for_complete(
            ClearImageCustomResourceLimitAction(
                image_canonical=key.image_canonical,
                architecture=key.architecture,
            )
        )
        return ClearImageCustomResourceLimitPayload(
            image_node=ImageNode.from_row(ctx, ImageRow.from_dataclass(result.image_data))
        )
