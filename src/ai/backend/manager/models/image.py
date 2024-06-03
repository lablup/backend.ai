from __future__ import annotations

import enum
import functools
import logging
from decimal import Decimal
from typing import (
    TYPE_CHECKING,
    Any,
    AsyncIterator,
    List,
    Mapping,
    MutableMapping,
    Optional,
    Sequence,
    Tuple,
    Union,
    cast,
    overload,
)
from uuid import UUID

import aiotools
import graphene
import sqlalchemy as sa
import trafaret as t
from graphql import Undefined
from redis.asyncio import Redis
from redis.asyncio.client import Pipeline
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import load_only, relationship, selectinload

from ai.backend.common import redis_helper
from ai.backend.common.docker import ImageRef
from ai.backend.common.etcd import AsyncEtcd
from ai.backend.common.exception import UnknownImageReference
from ai.backend.common.logging import BraceStyleAdapter
from ai.backend.common.types import BinarySize, ImageAlias, ResourceSlot

from ..api.exceptions import ImageNotFound, ObjectNotFound
from ..container_registry import get_container_registry_cls
from ..defs import DEFAULT_IMAGE_ARCH
from .base import (
    Base,
    BigInt,
    ForeignKeyIDColumn,
    IDColumn,
    KVPair,
    KVPairInput,
    ResourceLimit,
    ResourceLimitInput,
    StructuredJSONColumn,
    set_if_set,
)
from .gql_relay import AsyncNode
from .user import UserRole
from .utils import ExtendedAsyncSAEngine

if TYPE_CHECKING:
    from ai.backend.common.bgtask import ProgressReporter

    from ..config import SharedConfig
    from .gql import GraphQueryContext

log = BraceStyleAdapter(logging.getLogger(__spec__.name))  # type: ignore[name-defined]

__all__ = (
    "rescan_images",
    "ImageType",
    "ImageAliasRow",
    "ImageLoadFilter",
    "ImageRow",
    "Image",
    "PreloadImage",
    "PublicImageLoadFilter",
    "RescanImages",
    "ForgetImage",
    "ForgetImageById",
    "UntagImageFromRegistry",
    "ModifyImage",
    "AliasImage",
    "DealiasImage",
    "ClearImages",
)


class PublicImageLoadFilter(enum.StrEnum):
    OPERATIONAL = "operational"
    """Include operational images."""
    CUSTOMIZED = "customized"
    """Include customized images owned or accessible by API callee."""


class ImageLoadFilter(enum.StrEnum):
    OPERATIONAL = "operational"
    """Include operational images."""
    CUSTOMIZED = "customized"
    """Include customized images owned or accessible by API callee."""
    CUSTOMIZED_GLOBAL = "customized-global"
    """Include every customized images filed at the system. Effective only for superadmin. CUSTOMIZED and CUSTOMIZED_GLOBAL are mutually exclusive."""


async def rescan_images(
    etcd: AsyncEtcd,
    db: ExtendedAsyncSAEngine,
    registry_or_image: str | None = None,
    *,
    local: bool | None = False,
    reporter: ProgressReporter | None = None,
) -> None:
    # cannot import ai.backend.manager.config at start due to circular import
    from ..config import container_registry_iv

    if local:
        registries = {
            "local": {
                "": "http://localhost",
                "type": "local",
                "username": None,
                "password": None,
                "project": None,
            },
        }
    else:
        registry_config_iv = t.Mapping(t.String, container_registry_iv)
        latest_registry_config = cast(
            dict[str, Any],
            registry_config_iv.check(
                await etcd.get_prefix("config/docker/registry"),
            ),
        )
        # TODO: delete images from registries removed from the previous config?
        if registry_or_image is None:
            # scan all configured registries
            registries = latest_registry_config
        else:
            # find if it's a full image ref of one of configured registries
            for registry_name, registry_info in latest_registry_config.items():
                if registry_or_image.startswith(registry_name + "/"):
                    repo_with_tag = registry_or_image.removeprefix(registry_name + "/")
                    log.debug(
                        "running a per-image metadata scan: {}, {}",
                        registry_name,
                        repo_with_tag,
                    )
                    scanner_cls = get_container_registry_cls(registry_info)
                    scanner = scanner_cls(db, registry_name, registry_info)
                    await scanner.scan_single_ref(repo_with_tag)
                    return
            else:
                # treat it as a normal registry name
                registry = registry_or_image
                try:
                    registries = {registry: latest_registry_config[registry]}
                    log.debug("running a per-registry metadata scan")
                except KeyError:
                    raise RuntimeError("It is an unknown registry.", registry)
    async with aiotools.TaskGroup() as tg:
        for registry_name, registry_info in registries.items():
            log.info('Scanning kernel images from the registry "{0}"', registry_name)
            scanner_cls = get_container_registry_cls(registry_info)
            scanner = scanner_cls(db, registry_name, registry_info)
            tg.create_task(scanner.rescan_single_registry(reporter))
    # TODO: delete images removed from registry?


class ImageType(enum.Enum):
    COMPUTE = "compute"
    SYSTEM = "system"
    SERVICE = "service"


class ImageRow(Base):
    __tablename__ = "images"
    id = IDColumn("id")
    name = sa.Column("name", sa.String, nullable=False, index=True)
    image = sa.Column("image", sa.String, nullable=False, index=True)
    created_at = sa.Column(
        "created_at",
        sa.DateTime(timezone=True),
        server_default=sa.func.now(),
        index=True,
    )
    tag = sa.Column("tag", sa.TEXT)
    registry = sa.Column("registry", sa.String, nullable=False, index=True)
    architecture = sa.Column(
        "architecture", sa.String, nullable=False, index=True, default="x86_64"
    )
    config_digest = sa.Column("config_digest", sa.CHAR(length=72), nullable=False)
    size_bytes = sa.Column("size_bytes", sa.BigInteger, nullable=False)
    is_local = sa.Column(
        "is_local",
        sa.Boolean,
        nullable=False,
        server_default=sa.sql.expression.false(),
    )
    type = sa.Column("type", sa.Enum(ImageType), nullable=False)
    accelerators = sa.Column("accelerators", sa.String)
    labels = sa.Column("labels", sa.JSON, nullable=False)
    resources = sa.Column(
        "resources",
        StructuredJSONColumn(
            t.Mapping(
                t.String,
                t.Dict({
                    t.Key("min"): t.String,
                    t.Key("max", default=None): t.Null | t.String,
                }),
            ),
        ),
        nullable=False,
    )
    aliases: relationship
    # sessions = relationship("SessionRow", back_populates="image_row")
    endpoints = relationship("EndpointRow", back_populates="image_row")

    def __init__(
        self,
        name,
        architecture,
        is_local=False,
        registry=None,
        image=None,
        tag=None,
        config_digest=None,
        size_bytes=None,
        type=None,
        accelerators=None,
        labels=None,
        resources=None,
    ) -> None:
        self.name = name
        self.registry = registry
        self.image = image
        self.tag = tag
        self.architecture = architecture
        self.is_local = is_local
        self.config_digest = config_digest
        self.size_bytes = size_bytes
        self.type = type
        self.accelerators = accelerators
        self.labels = labels
        self.resources = resources

    @property
    def image_ref(self):
        return ImageRef(self.name, [self.registry], self.architecture, self.is_local)

    @classmethod
    async def from_alias(
        cls,
        session: AsyncSession,
        alias: str,
        load_aliases=False,
    ) -> ImageRow:
        query = (
            sa.select(ImageRow)
            .select_from(ImageRow)
            .join(ImageAliasRow, ImageRow.aliases.and_(ImageAliasRow.alias == alias))
        )
        if load_aliases:
            query = query.options(selectinload(ImageRow.aliases))
        result = await session.scalar(query)
        if result is not None:
            return result
        else:
            raise UnknownImageReference

    @classmethod
    async def from_image_ref(
        cls,
        session: AsyncSession,
        ref: ImageRef,
        *,
        strict_arch: bool = False,
        load_aliases: bool = False,
    ) -> ImageRow:
        """
        Loads a image row that corresponds to the given ImageRef object.

        When *strict_arch* is False and the image table has only one row
        with respect to requested canonical, this function will
        return that row regardless of the image architecture.
        """
        query = sa.select(ImageRow).where(ImageRow.name == ref.canonical)
        if load_aliases:
            query = query.options(selectinload(ImageRow.aliases))

        result = await session.execute(query)
        candidates: List[ImageRow] = result.scalars().all()

        if len(candidates) == 0:
            raise UnknownImageReference(ref)
        if len(candidates) == 1 and not strict_arch:
            return candidates[0]
        for row in candidates:
            if row.architecture == ref.architecture:
                return row
        raise UnknownImageReference(ref)

    @classmethod
    async def resolve(
        cls,
        session: AsyncSession,
        reference_candidates: List[Union[ImageAlias, ImageRef]],
        *,
        strict_arch: bool = False,
        load_aliases: bool = True,
    ) -> ImageRow:
        """
        Resolves a matching row in the image table from image references and/or aliases.
        If candidate element is `ImageRef`, this method will try to resolve image with matching
        `ImageRef` description. Otherwise, if element is `str`, this will try to follow the alias.
        If multiple elements are supplied, this method will return the first matched `ImageRow`
        among those elements.
        Passing the canonical image reference as string directly to resolve image data
        is no longer possible. You need to declare ImageRef object explicitly if you're using string
        as an canonical image references. For example:
        .. code-block::
           await ImageRow.resolve(
               conn,
               [
                   ImageRef(
                       image,
                       registry,
                       architecture,
                   ),
                   image_alias,
               ],
           )

        When *strict_arch* is False and the image table has only one row
        with respect to requested canonical, this function will
        return that row regardless of the image architecture.

        When *load_aliases* is True, it tries to resolve the alias chain.
        Otherwise it finds only the direct image references.
        """
        searched_refs = []
        for reference in reference_candidates:
            resolver_func: Any = None
            if isinstance(reference, str):
                resolver_func = cls.from_alias
                searched_refs.append(f"alias:{reference!r}")
            elif isinstance(reference, ImageRef):
                resolver_func = functools.partial(cls.from_image_ref, strict_arch=strict_arch)
                searched_refs.append(f"ref:{reference.canonical!r}")
            try:
                if row := await resolver_func(session, reference, load_aliases=load_aliases):
                    return row
            except UnknownImageReference:
                continue
        raise ImageNotFound("Unknown image references: " + ", ".join(searched_refs))

    @classmethod
    async def get(
        cls, session: AsyncSession, image_id: UUID, load_aliases=False
    ) -> ImageRow | None:
        query = sa.select(ImageRow).where(ImageRow.id == image_id)
        if load_aliases:
            query = query.options(selectinload(ImageRow.aliases))
        result = await session.execute(query)
        return result.scalar()

    @classmethod
    async def list(cls, session: AsyncSession, load_aliases=False) -> List[ImageRow]:
        query = sa.select(ImageRow)
        if load_aliases:
            query = query.options(selectinload(ImageRow.aliases))
        result = await session.execute(query)
        return result.scalars().all()

    def __str__(self) -> str:
        return self.image_ref.canonical + f" ({self.image_ref.architecture})"

    def __repr__(self) -> str:
        return self.__str__()

    async def get_slot_ranges(
        self,
        shared_config: SharedConfig,
    ) -> Tuple[ResourceSlot, ResourceSlot]:
        slot_units = await shared_config.get_resource_slots()
        min_slot = ResourceSlot()
        max_slot = ResourceSlot()

        for slot_key, resource in self.resources.items():
            slot_unit = slot_units.get(slot_key)
            if slot_unit is None:
                # ignore unknown slots
                continue
            min_value = resource.get("min")
            if min_value is None:
                min_value = Decimal(0)
            max_value = resource.get("max")
            if max_value is None:
                max_value = Decimal("Infinity")
            if slot_unit == "bytes":
                if not isinstance(min_value, Decimal):
                    min_value = BinarySize.from_str(min_value)
                if not isinstance(max_value, Decimal):
                    max_value = BinarySize.from_str(max_value)
            else:
                if not isinstance(min_value, Decimal):
                    min_value = Decimal(min_value)
                if not isinstance(max_value, Decimal):
                    max_value = Decimal(max_value)
            min_slot[slot_key] = min_value
            max_slot[slot_key] = max_value

        # fill missing
        for slot_key in slot_units.keys():
            if slot_key not in min_slot:
                min_slot[slot_key] = Decimal(0)
            if slot_key not in max_slot:
                max_slot[slot_key] = Decimal("Infinity")

        return min_slot, max_slot

    def _parse_row(self):
        res_limits = []
        for slot_key, slot_range in self.resources.items():
            min_value = slot_range.get("min")
            if min_value is None:
                min_value = Decimal(0)
            max_value = slot_range.get("max")
            if max_value is None:
                max_value = Decimal("Infinity")
            res_limits.append({
                "key": slot_key,
                "min": min_value,
                "max": max_value,
            })

        accels = self.accelerators
        if accels is None:
            accels = []
        else:
            accels = accels.split(",")

        return {
            "canonical_ref": self.name,
            "name": self.image,
            "humanized_name": self.image,  # TODO: implement
            "tag": self.tag,
            "architecture": self.architecture,
            "registry": self.registry,
            "digest": self.config_digest,
            "labels": self.labels,
            "size_bytes": self.size_bytes,
            "resource_limits": res_limits,
            "supported_accelerators": accels,
        }

    async def inspect(self) -> Mapping[str, Any]:
        parsed_image_info = self._parse_row()
        parsed_image_info["reverse_aliases"] = [x.alias for x in self.aliases]
        return parsed_image_info

    def set_resource_limit(
        self,
        slot_type: str,
        value_range: Tuple[Optional[Decimal], Optional[Decimal]],
    ):
        resources = self.resources
        if resources.get(slot_type) is None:
            resources[slot_type] = {}
        if value_range[0] is not None:
            resources[slot_type]["min"] = str(value_range[0])
        if value_range[1] is not None:
            resources[slot_type]["max"] = str(value_range[1])

        self.resources = resources


class ImageAliasRow(Base):
    __tablename__ = "image_aliases"
    id = IDColumn("id")
    alias = sa.Column("alias", sa.String, unique=True, index=True)
    image_id = ForeignKeyIDColumn("image", "images.id", nullable=False)
    image: relationship

    @classmethod
    async def create(
        cls,
        session: AsyncSession,
        alias: str,
        target: ImageRow,
    ) -> ImageAliasRow:
        existing_alias: Optional[ImageRow] = await session.scalar(
            sa.select(ImageAliasRow)
            .where(ImageAliasRow.alias == alias)
            .options(selectinload(ImageAliasRow.image)),
        )
        if existing_alias is not None:
            raise ValueError(
                f"alias already created with ({existing_alias.image})",
            )
        new_alias = ImageAliasRow(
            alias=alias,
            image_id=target.id,
        )
        session.add_all([new_alias])
        return new_alias


ImageRow.aliases = relationship("ImageAliasRow", back_populates="image")
ImageAliasRow.image = relationship("ImageRow", back_populates="aliases")


class Image(graphene.ObjectType):
    id = graphene.UUID()
    name = graphene.String()
    humanized_name = graphene.String()
    tag = graphene.String()
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
        ret = cls(
            id=row.id,
            name=row.image,
            humanized_name=row.image,
            tag=row.tag,
            registry=row.registry,
            architecture=row.architecture,
            is_local=row.is_local,
            digest=row.config_digest,
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
            hash=row.config_digest,
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
                row = await ImageRow.resolve(
                    session,
                    [
                        ImageRef(reference, ["*"], architecture),
                        ImageAlias(reference),
                    ],
                )
        except UnknownImageReference:
            raise ImageNotFound
        return await cls.from_row(ctx, row)

    @classmethod
    async def load_all(
        cls,
        ctx: GraphQueryContext,
        *,
        filters: set[ImageLoadFilter] = set(),
    ) -> Sequence[Image]:
        async with ctx.db.begin_readonly_session() as session:
            rows = await ImageRow.list(session, load_aliases=True)
        items: list[Image] = [
            item async for item in cls.bulk_load(ctx, rows) if item.matches_filter(ctx, filters)
        ]

        return items

    @staticmethod
    async def filter_allowed(
        ctx: GraphQueryContext,
        items: Sequence[Image],
        domain_name: str,
    ) -> Sequence[Image]:
        from .domain import domains

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
        filters: set[ImageLoadFilter],
    ) -> bool:
        """
        Determine if the image is filtered according to the `filters` parameter.
        """
        user_role = ctx.user["role"]

        if not filters:
            return True

        # If the image filtered by any of its labels, return False early.
        # If the image is not filtered and is determiend to be valid by any of its labels, `is_valid = True`.
        is_valid = False
        for label in self.labels:
            match label.key:
                case "ai.backend.features" if "operation" in label.value:
                    if ImageLoadFilter.OPERATIONAL in filters:
                        is_valid = True
                    else:
                        return False
                case "ai.backend.customized-image.owner":
                    if (
                        ImageLoadFilter.CUSTOMIZED not in filters
                        and ImageLoadFilter.CUSTOMIZED_GLOBAL not in filters
                    ):
                        return False
                    if ImageLoadFilter.CUSTOMIZED in filters:
                        if label.value == f"user:{ctx.user['uuid']}":
                            is_valid = True
                        else:
                            return False
                    if ImageLoadFilter.CUSTOMIZED_GLOBAL in filters:
                        if user_role == UserRole.SUPERADMIN:
                            is_valid = True
                        else:
                            return False
        return is_valid


class ImageNode(graphene.ObjectType):
    class Meta:
        interfaces = (AsyncNode,)

    row_id = graphene.UUID(description="Added in 24.03.4. The undecoded id value stored in DB.")
    name = graphene.String()
    humanized_name = graphene.String()
    tag = graphene.String()
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
        return cls(
            id=row.id,
            row_id=row.id,
            name=row.image,
            humanized_name=row.image,
            tag=row.tag,
            registry=row.registry,
            architecture=row.architecture,
            is_local=row.is_local,
            digest=row.config_digest,
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
            name=row.name,
            humanized_name=row.humanized_name,
            tag=row.tag,
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

    ok = graphene.Boolean()
    msg = graphene.String()
    task_id = graphene.UUID()

    @staticmethod
    async def mutate(
        root: Any,
        info: graphene.ResolveInfo,
        registry: str = None,
    ) -> RescanImages:
        log.info(
            "rescanning docker registry {0} by API request",
            f"({registry})" if registry else "(all)",
        )
        ctx: GraphQueryContext = info.context

        async def _rescan_task(reporter: ProgressReporter) -> None:
            await rescan_images(ctx.etcd, ctx.db, registry, reporter=reporter)

        task_id = await ctx.background_task_manager.start(_rescan_task)
        return RescanImages(ok=True, msg="", task_id=task_id)


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
                    ImageRef(reference, ["*"], architecture),
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

            registry_info = await ctx.shared_config.get_container_registry(
                image_row.image_ref.registry
            )
            if registry_info.get("type", "") != "harbor2":
                raise NotImplementedError("This feature is only supported for Harbor 2 registries")

        scanner = HarborRegistry_v2(ctx.db, image_row.image_ref.registry, registry_info)
        await scanner.untag(image_row.image_ref)

        return UntagImageFromRegistry(ok=True, msg="", image=ImageNode.from_row(image_row))


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
        image_ref = ImageRef(target, ["*"], architecture)
        log.info("alias image {0} -> {1} by API request", alias, image_ref)
        ctx: GraphQueryContext = info.context
        try:
            async with ctx.db.begin_session() as session:
                try:
                    image_row = await ImageRow.from_image_ref(session, image_ref, load_aliases=True)
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

        if props.resource_limits is not None:
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
                image_ref = ImageRef(target, ["*"], architecture)
                try:
                    row = await ImageRow.from_image_ref(session, image_ref)
                except UnknownImageReference:
                    return ModifyImage(ok=False, msg="Image not found")
                for k, v in data.items():
                    setattr(row, k, v)
        except ValueError as e:
            return ModifyImage(ok=False, msg=str(e))
        return ModifyImage(ok=True, msg="")


class ImageRefType(graphene.InputObjectType):
    name = graphene.String(required=True)
    registry = graphene.String()
    architecture = graphene.String()
