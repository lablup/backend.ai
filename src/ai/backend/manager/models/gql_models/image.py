from __future__ import annotations

import logging
from collections.abc import MutableMapping, Sequence
from decimal import Decimal
from typing import (
    TYPE_CHECKING,
    Any,
    AsyncIterator,
    List,
    Optional,
    overload,
)
from uuid import UUID

import graphene
import sqlalchemy as sa
from graphql import Undefined
from redis.asyncio import Redis
from redis.asyncio.client import Pipeline
from sqlalchemy.orm import load_only, selectinload

from ai.backend.common import redis_helper
from ai.backend.common.docker import ImageRef
from ai.backend.common.exception import UnknownImageReference
from ai.backend.common.types import (
    ImageAlias,
)
from ai.backend.logging import BraceStyleAdapter
from ai.backend.manager.models.container_registry import ContainerRegistryRow, ContainerRegistryType

from ...api.exceptions import ImageNotFound, ObjectNotFound
from ...defs import DEFAULT_IMAGE_ARCH
from ..base import batch_multiresult_in_scalar_stream, set_if_set
from ..gql_relay import AsyncNode
from ..image import (
    ImageAliasRow,
    ImageIdentifier,
    ImageLoadFilter,
    ImageRow,
    rescan_images,
)
from ..user import UserRole
from .base import (
    BigInt,
    KVPair,
    KVPairInput,
    ResourceLimit,
    ResourceLimitInput,
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
    "UntagImageFromRegistry",
    "ModifyImage",
    "AliasImage",
    "DealiasImage",
    "ClearImages",
)


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
    ) -> Sequence[Optional[Image]]:
        query = (
            sa.select(ImageRow)
            .where(ImageRow.name.in_(image_names))
            .options(selectinload(ImageRow.aliases))
        )
        async with graph_ctx.db.begin_readonly_session() as session:
            result = await session.execute(query)
            return [await Image.from_row(graph_ctx, row) for row in result.scalars().all()]

    @classmethod
    async def batch_load_by_image_ref(
        cls,
        graph_ctx: GraphQueryContext,
        image_refs: Sequence[ImageRef],
    ) -> Sequence[Optional[Image]]:
        image_names = [x.canonical for x in image_refs]
        return await cls.batch_load_by_canonical(graph_ctx, image_names)

    @classmethod
    async def load_item_by_id(
        cls,
        ctx: GraphQueryContext,
        id: UUID,
    ) -> Image:
        async with ctx.db.begin_readonly_session() as session:
            row = await ImageRow.get(session, id, load_aliases=True)
            if not row:
                raise ImageNotFound

            return await cls.from_row(ctx, row)

    @classmethod
    async def load_item(
        cls,
        ctx: GraphQueryContext,
        reference: str,
        architecture: str,
    ) -> Image:
        try:
            async with ctx.db.begin_readonly_session() as session:
                image_row = await ImageRow.resolve(
                    session,
                    [
                        ImageIdentifier(reference, architecture),
                        ImageAlias(reference),
                    ],
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
    ) -> Sequence[Image]:
        async with ctx.db.begin_readonly_session() as session:
            rows = await ImageRow.list(session, load_aliases=True)
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
    resource_limits = graphene.List(ResourceLimit)
    supported_accelerators = graphene.List(graphene.String)
    aliases = graphene.List(
        graphene.String, description="Added in 24.03.4. The array of image aliases."
    )

    @classmethod
    async def batch_load_by_name_and_arch(
        cls,
        graph_ctx: GraphQueryContext,
        name_and_arch: Sequence[tuple[str, str]],
    ) -> Sequence[Sequence[ImageNode]]:
        query = (
            sa.select(ImageRow)
            .where(sa.tuple_(ImageRow.name, ImageRow.architecture).in_(name_and_arch))
            .options(selectinload(ImageRow.aliases))
        )
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
    ) -> Sequence[Sequence[ImageNode]]:
        name_and_arch_tuples = [(img.canonical, img.architecture) for img in image_ids]
        return await cls.batch_load_by_name_and_arch(graph_ctx, name_and_arch_tuples)

    @overload
    @classmethod
    def from_row(cls, row: ImageRow) -> ImageNode: ...

    @overload
    @classmethod
    def from_row(cls, row: None) -> None: ...

    @classmethod
    def from_row(cls, row: ImageRow | None) -> ImageNode | None:
        if row is None:
            return None
        image_ref = row.image_ref
        version, ptag_set = image_ref.tag_set
        return cls(
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
        )

    @classmethod
    def from_legacy_image(cls, row: Image) -> ImageNode:
        return cls(
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
        )

    @classmethod
    async def get_node(cls, info: graphene.ResolveInfo, id: str) -> ImageNode:
        graph_ctx: GraphQueryContext = info.context

        _, image_id = AsyncNode.resolve_global_id(info, id)
        query = (
            sa.select(ImageRow)
            .where(ImageRow.id == image_id)
            .options(selectinload(ImageRow.aliases).options(load_only(ImageAliasRow.alias)))
        )
        async with graph_ctx.db.begin_readonly_session() as db_session:
            image_row = await db_session.scalar(query)
            if image_row is None:
                raise ValueError(f"Image not found (id: {image_id})")
            return cls.from_row(image_row)


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
        _, raw_image_id = AsyncNode.resolve_global_id(info, image_id)
        if not raw_image_id:
            raw_image_id = image_id

        try:
            _image_id = UUID(raw_image_id)
        except ValueError:
            raise ObjectNotFound("image")

        log.info("forget image {0} by API request", image_id)
        ctx: GraphQueryContext = info.context
        client_role = ctx.user["role"]

        async with ctx.db.begin_session() as session:
            image_row = await ImageRow.get(session, _image_id, load_aliases=True)
            if not image_row:
                raise ObjectNotFound("image")
            if client_role != UserRole.SUPERADMIN:
                customized_image_owner = (image_row.labels or {}).get(
                    "ai.backend.customized-image.owner"
                )
                if (
                    not customized_image_owner
                    or customized_image_owner != f"user:{ctx.user['uuid']}"
                ):
                    return ForgetImageById(ok=False, msg="Forbidden")
            await session.delete(image_row)
            return ForgetImageById(ok=True, msg="", image=ImageNode.from_row(image_row))


class ForgetImage(graphene.Mutation):
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
                customized_image_owner = (image_row.labels or {}).get(
                    "ai.backend.customized-image.owner"
                )
                if (
                    not customized_image_owner
                    or customized_image_owner != f"user:{ctx.user['uuid']}"
                ):
                    return ForgetImage(ok=False, msg="Forbidden")
            await session.delete(image_row)
            return ForgetImage(ok=True, msg="", image=ImageNode.from_row(image_row))


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

        _, raw_image_id = AsyncNode.resolve_global_id(info, image_id)
        if not raw_image_id:
            raw_image_id = image_id

        try:
            _image_id = UUID(raw_image_id)
        except ValueError:
            raise ObjectNotFound("image")

        log.info("remove image from registry {0} by API request", str(_image_id))
        ctx: GraphQueryContext = info.context
        client_role = ctx.user["role"]

        async with ctx.db.begin_readonly_session() as session:
            image_row = await ImageRow.get(session, _image_id, load_aliases=True)
            if not image_row:
                raise ImageNotFound
            if client_role != UserRole.SUPERADMIN:
                customized_image_owner = (image_row.labels or {}).get(
                    "ai.backend.customized-image.owner"
                )
                if (
                    not customized_image_owner
                    or customized_image_owner != f"user:{ctx.user['uuid']}"
                ):
                    return UntagImageFromRegistry(ok=False, msg="Forbidden")

            query = sa.select(ContainerRegistryRow).where(
                ContainerRegistryRow.registry_name == image_row.image_ref.registry
            )

            registry_info = (await session.execute(query)).scalar()

            if registry_info.type != ContainerRegistryType.HARBOR2:
                raise NotImplementedError("This feature is only supported for Harbor 2 registries")

        scanner = HarborRegistry_v2(ctx.db, image_row.image_ref.registry, registry_info)
        await scanner.untag(image_row.image_ref)

        return UntagImageFromRegistry(ok=True, msg="", image=ImageNode.from_row(image_row))


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

        async def _rescan_task(reporter: ProgressReporter) -> None:
            await rescan_images(ctx.db, registry, project, reporter=reporter)

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
                result = await session.execute(
                    sa.select(ImageRow).where(ImageRow.registry == registry)
                )
                image_ids = [x.id for x in result.scalars().all()]

                await session.execute(
                    sa.delete(ImageAliasRow).where(ImageAliasRow.image_id.in_(image_ids))
                )
                await session.execute(sa.delete(ImageRow).where(ImageRow.registry == registry))
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
