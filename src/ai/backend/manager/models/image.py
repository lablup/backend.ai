from __future__ import annotations

import enum
import functools
import logging
import uuid
from collections.abc import Iterable, Mapping
from dataclasses import dataclass
from decimal import Decimal
from typing import (
    TYPE_CHECKING,
    Any,
    Callable,
    List,
    NamedTuple,
    Optional,
    Tuple,
    TypeAlias,
    cast,
    override,
)
from uuid import UUID

import sqlalchemy as sa
import trafaret as t
from sqlalchemy.ext.asyncio import AsyncConnection, AsyncSession
from sqlalchemy.orm import foreign, joinedload, load_only, relationship, selectinload
from sqlalchemy.sql.expression import true

from ai.backend.common.docker import ImageRef
from ai.backend.common.exception import UnknownImageReference
from ai.backend.common.types import (
    AutoPullBehavior,
    BinarySize,
    DispatchResult,
    ImageAlias,
    ImageConfig,
    ImageRegistry,
    ResourceSlot,
)
from ai.backend.common.utils import join_non_empty
from ai.backend.logging import BraceStyleAdapter

from ..api.exceptions import ImageNotFound
from ..container_registry import get_container_registry_cls
from ..models.container_registry import ContainerRegistryRow
from .base import (
    GUID,
    Base,
    ForeignKeyIDColumn,
    IDColumn,
    StrEnumType,
    StructuredJSONColumn,
)
from .rbac import (
    AbstractPermissionContext,
    AbstractPermissionContextBuilder,
    DomainScope,
    ProjectScope,
    ScopeType,
    UserScope,
    get_predefined_roles_in_scope,
)
from .rbac.context import ClientContext
from .rbac.exceptions import InvalidScope
from .rbac.permission_defs import ImagePermission
from .user import UserRole, UserRow
from .utils import ExtendedAsyncSAEngine

if TYPE_CHECKING:
    from ai.backend.common.bgtask import ProgressReporter

    from ..config import SharedConfig

log = BraceStyleAdapter(logging.getLogger(__spec__.name))


__all__ = (
    "rescan_images",
    "ImageType",
    "ImageAliasRow",
    "ImageLoadFilter",
    "ImageRow",
    "ImageIdentifier",
    "PublicImageLoadFilter",
)


class ImageIdentifier(NamedTuple):
    """
    Represent a tuple of image's canonical string and architecture, uniquely corresponding to an ImageRow.
    """

    canonical: str
    architecture: str


class PublicImageLoadFilter(enum.StrEnum):
    """Shorthand of `ImageLoadFilter` enum with `CUSTOMIZED_GLOBAL` removed (as it is not intended for API input)."""

    GENERAL = "general"
    """Include general purpose images."""
    OPERATIONAL = "operational"
    """Include operational images."""
    CUSTOMIZED = "customized"
    """Include customized images owned or accessible by API callee."""


class ImageLoadFilter(enum.StrEnum):
    """Enum describing kind of a "search preset" when loading Image data via GQL. Not intended for declaring attributes of image data itself."""

    GENERAL = "general"
    """Include general purpose images."""
    OPERATIONAL = "operational"
    """Include operational images."""
    CUSTOMIZED = "customized"
    """Include customized images owned or accessible by API callee."""
    CUSTOMIZED_GLOBAL = "customized-global"
    """Include every customized images filed at the system. Effective only for superadmin. CUSTOMIZED and CUSTOMIZED_GLOBAL are mutually exclusive."""


class RelationLoadingOption(enum.StrEnum):
    ALIASES = enum.auto()
    ENDPOINTS = enum.auto()
    REGISTRY = enum.auto()


def _apply_loading_option(
    query_stmt: sa.sql.Select, options: Iterable[RelationLoadingOption]
) -> sa.sql.Select:
    for op in options:
        match op:
            case RelationLoadingOption.ALIASES:
                query_stmt = query_stmt.options(selectinload(ImageRow.aliases))
            case RelationLoadingOption.REGISTRY:
                query_stmt = query_stmt.options(joinedload(ImageRow.registry_row))
            case RelationLoadingOption.ENDPOINTS:
                query_stmt = query_stmt.options(selectinload(ImageRow.endpoints))
    return query_stmt


async def load_configured_registries(
    db: ExtendedAsyncSAEngine,
    project: Optional[str],
) -> dict[str, ContainerRegistryRow]:
    join = functools.partial(join_non_empty, sep="/")

    async with db.begin_readonly_session() as session:
        result = await session.execute(sa.select(ContainerRegistryRow))
        if project:
            registries = cast(
                dict[str, ContainerRegistryRow],
                {
                    join(row.registry_name, row.project): row
                    for row in result.scalars().all()
                    if row.project == project
                },
            )
        else:
            registries = cast(
                dict[str, ContainerRegistryRow],
                {join(row.registry_name, row.project): row for row in result.scalars().all()},
            )

    return cast(dict[str, ContainerRegistryRow], registries)


async def scan_registries(
    db: ExtendedAsyncSAEngine,
    registries: dict[str, ContainerRegistryRow],
    reporter: Optional[ProgressReporter] = None,
) -> DispatchResult[list[ImageRow]]:
    """
    Performs an image rescan for all images in the registries.
    """
    images, errors = [], []

    for registry_key, registry_row in registries.items():
        registry_name = ImageRef.parse_image_str(registry_key, "*").registry
        log.info('Scanning kernel images from the registry "{0}"', registry_name)

        scanner_cls = get_container_registry_cls(registry_row)
        scanner = scanner_cls(db, registry_name, registry_row)

        try:
            scan_result = await scanner.rescan_single_registry(reporter)
            images.extend(scan_result.result or [])
            errors.extend(scan_result.errors or [])
        except Exception as e:
            errors.append(str(e))

    return DispatchResult(result=images, errors=errors)


async def scan_single_image(
    db: ExtendedAsyncSAEngine,
    registry_key: str,
    registry_row: ContainerRegistryRow,
    image_canonical: str,
) -> DispatchResult[list[ImageRow]]:
    """
    Performs a scan for a single image.
    """
    registry_name = ImageRef.parse_image_str(registry_key, "*").registry
    image_name = image_canonical.removeprefix(registry_name + "/")

    log.debug("running a per-image metadata scan: {}, {}", registry_name, image_name)

    scanner_cls = get_container_registry_cls(registry_row)
    scanner = scanner_cls(db, registry_name, registry_row)
    return await scanner.scan_single_ref(image_name)


def filter_registry_dict(
    registries: dict[str, ContainerRegistryRow],
    condition: Callable[[str, ContainerRegistryRow], bool],
) -> dict[str, ContainerRegistryRow]:
    return {
        registry_key: registry_row
        for registry_key, registry_row in registries.items()
        if condition(registry_key, registry_row)
    }


def filter_registries_by_img_canonical(
    registries: dict[str, ContainerRegistryRow], registry_or_image: str
) -> dict[str, ContainerRegistryRow]:
    """
    Filters the matching registry assuming `registry_or_image` is an image canonical name.
    """
    return filter_registry_dict(
        registries,
        lambda registry_key, _row: registry_or_image.startswith(registry_key + "/"),
    )


def filter_registries_by_registry_name(
    registries: dict[str, ContainerRegistryRow], registry_or_image: str
) -> dict[str, ContainerRegistryRow]:
    """
    Filters the matching registry assuming `registry_or_image` is a registry name.
    """
    return filter_registry_dict(
        registries,
        lambda registry_key, _row: registry_key.startswith(registry_or_image),
    )


async def rescan_images(
    db: ExtendedAsyncSAEngine,
    registry_or_image: Optional[str] = None,
    project: Optional[str] = None,
    *,
    reporter: Optional[ProgressReporter] = None,
) -> DispatchResult[list[ImageRow]]:
    """
    Rescan container registries and the update images table.
    Refer to the comments below for details on the function's behavior.

    If registry name is provided for `registry_or_image`, scans all images in the specified registry.
    If image canonical name is provided for `registry_or_image`, only scan the image.
    If the `registry_or_image` is not provided, scan all configured registries.

    If `project` is provided, only scan the registries associated with the project.
    """
    registries = await load_configured_registries(db, project)

    if registry_or_image is None:
        return await scan_registries(db, registries, reporter=reporter)

    matching_registries = filter_registries_by_img_canonical(registries, registry_or_image)

    if matching_registries:
        if len(matching_registries) > 1:
            raise RuntimeError(
                "ContainerRegistryRows exist with the same registry_name and project!",
            )

        registry_key, registry_row = next(iter(matching_registries.items()))
        return await scan_single_image(db, registry_key, registry_row, registry_or_image)

    matching_registries = filter_registries_by_registry_name(registries, registry_or_image)

    if not matching_registries:
        raise RuntimeError("It is an unknown registry.", registry_or_image)

    log.debug("running a per-registry metadata scan")
    return await scan_registries(db, matching_registries, reporter=reporter)
    # TODO: delete images removed from registry?


class ImageType(enum.Enum):
    COMPUTE = "compute"
    SYSTEM = "system"
    SERVICE = "service"


# Defined for avoiding circular import
def _get_image_endpoint_join_condition():
    from ai.backend.manager.models.endpoint import EndpointRow

    return ImageRow.id == foreign(EndpointRow.image)


class ImageStatus(enum.StrEnum):
    ALIVE = "ALIVE"
    DELETED = "DELETED"


class ImageRow(Base):
    __tablename__ = "images"
    __table_args__ = (
        sa.UniqueConstraint(
            "registry", "project", "name", "tag", "architecture", name="uq_image_identifier"
        ),
    )

    id = IDColumn("id")
    name = sa.Column("name", sa.String, nullable=False, index=True)
    project = sa.Column("project", sa.String, nullable=True)
    image = sa.Column("image", sa.String, nullable=False, index=True)
    created_at = sa.Column(
        "created_at",
        sa.DateTime(timezone=True),
        server_default=sa.func.now(),
        index=True,
    )
    tag = sa.Column("tag", sa.TEXT)
    registry = sa.Column("registry", sa.String, nullable=False, index=True)
    registry_id = sa.Column("registry_id", GUID, nullable=False, index=True)
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
    labels = sa.Column("labels", sa.JSON, nullable=False, default=dict)
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
    status = sa.Column(
        "status",
        StrEnumType(ImageStatus),
        default=ImageStatus.ALIVE,
        server_default=ImageStatus.ALIVE.name,
        nullable=False,
    )

    aliases: relationship
    # sessions = relationship("SessionRow", back_populates="image_row")
    endpoints = relationship(
        "EndpointRow",
        primaryjoin=_get_image_endpoint_join_condition,
        back_populates="image_row",
    )

    registry_row = relationship(
        "ContainerRegistryRow",
        back_populates="image_rows",
        primaryjoin="ContainerRegistryRow.id == foreign(ImageRow.registry_id)",
    )

    def __init__(
        self,
        name,
        project,
        architecture,
        registry_id,
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
        status=ImageStatus.ALIVE,
    ) -> None:
        self.name = name
        self.project = project
        self.registry = registry
        self.registry_id = registry_id
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
        self.status = status

    @property
    def trimmed_digest(self) -> str:
        return self.config_digest.strip()

    @property
    def image_ref(self) -> ImageRef:
        # Empty image name
        if self.project == self.image:
            image_name = ""
            _, tag = ImageRef.parse_image_tag(self.name.split(f"{self.registry}/", maxsplit=1)[1])
        else:
            join = functools.partial(join_non_empty, sep="/")
            image_and_tag = self.name.removeprefix(f"{join(self.registry, self.project)}/")
            image_name, tag = ImageRef.parse_image_tag(image_and_tag)

        return ImageRef(
            image_name, self.project, tag, self.registry, self.architecture, self.is_local
        )

    @classmethod
    async def from_alias(
        cls,
        session: AsyncSession,
        alias: str,
        load_aliases: bool = False,
        filter_by_statuses: Optional[list[ImageStatus]] = [ImageStatus.ALIVE],
        *,
        loading_options: Iterable[RelationLoadingOption] = tuple(),
    ) -> ImageRow:
        query = (
            sa.select(ImageRow)
            .select_from(ImageRow)
            .join(ImageAliasRow, ImageRow.aliases.and_(ImageAliasRow.alias == alias))
        )
        if load_aliases:
            query = query.options(selectinload(ImageRow.aliases))
        if filter_by_statuses:
            query = query.where(ImageRow.status.in_(filter_by_statuses))

        query = _apply_loading_option(query, loading_options)
        result = await session.scalar(query)
        if result is not None:
            return result
        else:
            raise UnknownImageReference

    @classmethod
    async def from_image_identifier(
        cls,
        session: AsyncSession,
        identifier: ImageIdentifier,
        load_aliases: bool = True,
        filter_by_statuses: Optional[list[ImageStatus]] = [ImageStatus.ALIVE],
        *,
        loading_options: Iterable[RelationLoadingOption] = tuple(),
    ) -> ImageRow:
        query = sa.select(ImageRow).where(
            (ImageRow.name == identifier.canonical)
            & (ImageRow.architecture == identifier.architecture)
        )

        if load_aliases:
            query = query.options(selectinload(ImageRow.aliases))
        if filter_by_statuses:
            query = query.where(ImageRow.status.in_(filter_by_statuses))

        query = _apply_loading_option(query, loading_options)

        result = await session.execute(query)
        candidates: List[ImageRow] = result.scalars().all()

        if len(candidates) <= 0:
            raise UnknownImageReference(identifier.canonical)

        return candidates[0]

    @classmethod
    async def from_image_ref(
        cls,
        session: AsyncSession,
        ref: ImageRef,
        *,
        strict_arch: bool = False,
        load_aliases: bool = False,
        filter_by_statuses: Optional[list[ImageStatus]] = [ImageStatus.ALIVE],
        loading_options: Iterable[RelationLoadingOption] = tuple(),
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
        if filter_by_statuses:
            query = query.where(ImageRow.status.in_(filter_by_statuses))

        query = _apply_loading_option(query, loading_options)

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
        reference_candidates: list[ImageAlias | ImageRef | ImageIdentifier],
        *,
        strict_arch: bool = False,
        filter_by_statuses: Optional[list[ImageStatus]] = [ImageStatus.ALIVE],
        load_aliases: bool = True,
        loading_options: Iterable[RelationLoadingOption] = tuple(),
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
                       image_name,
                       project,
                       registry,
                       tag,
                       architecture,
                       is_local,
                   ),
                   ImageIdentifier(canonical, architecture),
                   ImageAlias(image_alias),
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
            elif isinstance(reference, ImageIdentifier):
                resolver_func = cls.from_image_identifier
                searched_refs.append(f"identifier:{reference!r}")
            try:
                if row := await resolver_func(
                    session,
                    reference,
                    load_aliases=load_aliases,
                    filter_by_statuses=filter_by_statuses,
                    loading_options=loading_options,
                ):
                    return row
            except UnknownImageReference:
                continue
        raise ImageNotFound("Unknown image references: " + ", ".join(searched_refs))

    @classmethod
    async def get(
        cls,
        session: AsyncSession,
        image_id: UUID,
        filter_by_statuses: Optional[list[ImageStatus]] = [ImageStatus.ALIVE],
        load_aliases: bool = False,
    ) -> ImageRow | None:
        query = sa.select(ImageRow).where(ImageRow.id == image_id)
        if load_aliases:
            query = query.options(selectinload(ImageRow.aliases))
        if filter_by_statuses:
            query = query.where(ImageRow.status.in_(filter_by_statuses))

        result = await session.execute(query)
        return result.scalar()

    @classmethod
    async def list(
        cls,
        session: AsyncSession,
        filter_by_statuses: Optional[list[ImageStatus]] = [ImageStatus.ALIVE],
        load_aliases: bool = False,
    ) -> List[ImageRow]:
        query = sa.select(ImageRow)
        if load_aliases:
            query = query.options(selectinload(ImageRow.aliases))
        if filter_by_statuses:
            query = query.where(ImageRow.status.in_(filter_by_statuses))

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
        # When the original image does not have any metadata label, self.resources is already filled
        # with the intrinsic resource slots with their defualt minimums (defs.INTRINSIC_SLOTS_MIN)
        # during rescanning the registry.
        assert self.resources is not None

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
        assert self.resources is not None
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
            "digest": self.trimmed_digest or None,
            "labels": self.labels,
            "size_bytes": self.size_bytes,
            "resource_limits": res_limits,
            "supported_accelerators": accels,
        }

    async def inspect(self) -> Mapping[str, Any]:
        parsed_image_info = self._parse_row()
        parsed_image_info["reverse_aliases"] = [x.alias for x in self.aliases]
        return parsed_image_info

    async def mark_as_deleted(self, db_session: AsyncSession) -> None:
        self.status = ImageStatus.DELETED
        await db_session.flush()

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

    def is_customized_by(self, user_id: str) -> bool:
        return (self.labels or {}).get("ai.backend.customized-image.owner") == f"user:{user_id}"


async def bulk_get_image_configs(
    image_refs: Iterable[ImageRef],
    auto_pull: AutoPullBehavior = AutoPullBehavior.DIGEST,
    *,
    db_session: AsyncSession,
) -> list[ImageConfig]:
    result: list[ImageConfig] = []

    for ref in image_refs:
        resolved_image_info = await ImageRow.resolve(db_session, [ref])

        registry_info: ImageRegistry
        if resolved_image_info.image_ref.is_local:
            registry_info = {
                "name": ref.registry,
                "url": "http://127.0.0.1",  # "http://localhost",
                "username": None,
                "password": None,
            }
        else:
            url, credential = await ContainerRegistryRow.get_container_registry_info(
                db_session, resolved_image_info.registry_id
            )
            registry_info = {
                "name": ref.registry,
                "url": str(url),
                "username": credential["username"],
                "password": credential["password"],
            }

        image_conf: ImageConfig = {
            "architecture": ref.architecture,
            "project": resolved_image_info.project,
            "canonical": ref.canonical,
            "is_local": resolved_image_info.image_ref.is_local,
            "digest": resolved_image_info.trimmed_digest,
            "labels": resolved_image_info.labels,
            "repo_digest": None,
            "registry": registry_info,
            "auto_pull": auto_pull,
        }

        result.append(image_conf)

    return result


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


WhereClauseType: TypeAlias = (
    sa.sql.expression.BinaryExpression | sa.sql.expression.BooleanClauseList
)
# TypeAlias is deprecated since 3.12 but mypy does not follow up yet

ALL_IMAGE_PERMISSIONS = frozenset([perm for perm in ImagePermission])
OWNER_PERMISSIONS: frozenset[ImagePermission] = ALL_IMAGE_PERMISSIONS
ADMIN_PERMISSIONS: frozenset[ImagePermission] = frozenset([
    ImagePermission.READ_ATTRIBUTE,
    ImagePermission.CREATE_CONTAINER,
])
MONITOR_PERMISSIONS: frozenset[ImagePermission] = frozenset([
    ImagePermission.READ_ATTRIBUTE,
    ImagePermission.UPDATE_ATTRIBUTE,
])
PRIVILEGED_MEMBER_PERMISSIONS: frozenset[ImagePermission] = frozenset([
    ImagePermission.READ_ATTRIBUTE,
    ImagePermission.CREATE_CONTAINER,
])
MEMBER_PERMISSIONS: frozenset[ImagePermission] = frozenset([
    ImagePermission.READ_ATTRIBUTE,
    ImagePermission.CREATE_CONTAINER,
])


@dataclass
class ImagePermissionContext(AbstractPermissionContext[ImagePermission, ImageRow, UUID]):
    @property
    def query_condition(self) -> Optional[WhereClauseType]:
        cond: WhereClauseType | None = None

        def _OR_coalesce(
            base_cond: Optional[WhereClauseType],
            _cond: sa.sql.expression.BinaryExpression,
        ) -> WhereClauseType:
            return base_cond | _cond if base_cond is not None else _cond

        if self.object_id_to_additional_permission_map:
            cond = _OR_coalesce(
                cond, ImageRow.id.in_(self.object_id_to_additional_permission_map.keys())
            )
        if self.object_id_to_overriding_permission_map:
            cond = _OR_coalesce(
                cond, ImageRow.id.in_(self.object_id_to_overriding_permission_map.keys())
            )
        return cond

    async def build_query(self) -> Optional[sa.sql.Select]:
        cond = self.query_condition
        if cond is None:
            return None
        return sa.select(ImageRow).where(cond)

    async def calculate_final_permission(self, rbac_obj: ImageRow) -> frozenset[ImagePermission]:
        image_row = rbac_obj
        image_id = cast(UUID, image_row.id)
        permissions: set[ImagePermission] = set()

        if (
            overriding_perm := self.object_id_to_overriding_permission_map.get(image_id)
        ) is not None:
            permissions = set(overriding_perm)
        else:
            permissions |= self.object_id_to_additional_permission_map.get(image_id, set())

        return frozenset(permissions)


class ImagePermissionContextBuilder(
    AbstractPermissionContextBuilder[ImagePermission, ImagePermissionContext]
):
    db_session: AsyncSession

    def __init__(self, db_session: AsyncSession) -> None:
        self.db_session = db_session

    @override
    async def calculate_permission(
        self,
        ctx: ClientContext,
        target_scope: ScopeType,
    ) -> frozenset[ImagePermission]:
        roles = await get_predefined_roles_in_scope(ctx, target_scope, self.db_session)
        permissions = await self._calculate_permission_by_predefined_roles(roles)
        permissions |= await self.apply_customized_role(ctx, target_scope)
        return permissions

    async def apply_customized_role(
        self,
        ctx: ClientContext,
        target_scope: ScopeType,
    ) -> frozenset[ImagePermission]:
        if ctx.user_role == UserRole.SUPERADMIN:
            return ALL_IMAGE_PERMISSIONS
        return frozenset()

    @override
    async def build_ctx_in_system_scope(
        self,
        ctx: ClientContext,
    ) -> ImagePermissionContext:
        perm_ctx = ImagePermissionContext()
        user_accessible_project_scopes = await self._get_user_accessible_project_scopes(
            ctx, UserScope(ctx.user_id)
        )
        global_project_scopes_perm_ctx = await self._in_project_scopes_global(
            ctx, user_accessible_project_scopes
        )
        perm_ctx.merge(global_project_scopes_perm_ctx)
        non_global_project_scopes_perm_ctx = await self._in_project_scopes_non_global(
            ctx, user_accessible_project_scopes
        )
        perm_ctx.merge(non_global_project_scopes_perm_ctx)
        user_scope_perm_ctx = await self._in_user_scope(ctx, UserScope(ctx.user_id))
        perm_ctx.merge(user_scope_perm_ctx)
        return perm_ctx

    @override
    async def build_ctx_in_domain_scope(
        self,
        ctx: ClientContext,
        scope: DomainScope,
    ) -> ImagePermissionContext:
        perm_ctx = ImagePermissionContext()
        domain_scope_perm_ctx = await self._in_domain_scope(ctx, scope)
        perm_ctx.merge(domain_scope_perm_ctx)
        user_scope_perm_ctx = await self._in_user_scope(ctx, UserScope(ctx.user_id))
        perm_ctx.merge(user_scope_perm_ctx)

        project_scopes = await self._get_domain_accessible_project_scopes(ctx, scope)
        non_global_container_registries_perm_ctx = await self._in_project_scopes_non_global(
            ctx, project_scopes
        )
        perm_ctx.merge(non_global_container_registries_perm_ctx)
        return perm_ctx

    @override
    async def build_ctx_in_project_scope(
        self,
        ctx: ClientContext,
        scope: ProjectScope,
    ) -> ImagePermissionContext:
        perm_ctx = ImagePermissionContext()
        global_container_registries_perm_ctx = await self._in_project_scopes_global(ctx, [scope])
        perm_ctx.merge(global_container_registries_perm_ctx)
        non_global_container_registries_perm_ctx = await self._in_project_scopes_non_global(
            ctx, [scope]
        )
        perm_ctx.merge(non_global_container_registries_perm_ctx)
        return perm_ctx

    @override
    async def build_ctx_in_user_scope(
        self,
        ctx: ClientContext,
        scope: UserScope,
    ) -> ImagePermissionContext:
        perm_ctx = ImagePermissionContext()
        user_scope_perm_ctx = await self._in_user_scope(ctx, scope)
        perm_ctx.merge(user_scope_perm_ctx)

        project_scopes = await self._get_user_accessible_project_scopes(ctx, scope)

        # We should fetch only customized images
        non_global_container_registries_perm_ctx = await self._in_project_scopes_non_global(
            ctx, project_scopes, True
        )
        perm_ctx.merge(non_global_container_registries_perm_ctx)
        return perm_ctx

    async def _get_allowed_registries_for_user(
        self, ctx: ClientContext, user_id: uuid.UUID
    ) -> set[str]:
        _user_query_stmt = (
            sa.select(UserRow).where(UserRow.uuid == user_id).options(joinedload(UserRow.domain))
        )
        user_row = cast(Optional[UserRow], await self.db_session.scalar(_user_query_stmt))
        if user_row is None:
            raise InvalidScope(f"User not found (id:{user_id})")
        return set(user_row.domain.allowed_docker_registries)

    def _is_image_accessible_for_user(
        self, image: ImageRow, allowed_registries: set[str], user_id: uuid.UUID
    ) -> bool:
        if image.registry not in allowed_registries:
            return False
        labels = cast(dict[str, str], image.labels)
        if labels.get("ai.backend.customized-image.owner") != f"user:{user_id}":
            return False
        return True

    async def _in_user_scope(
        self,
        ctx: ClientContext,
        scope: UserScope,
    ) -> ImagePermissionContext:
        allowed_registries = await self._get_allowed_registries_for_user(ctx, scope.user_id)

        permissions = await self.calculate_permission(ctx, scope)
        image_id_permission_map: dict[UUID, frozenset[ImagePermission]] = {}

        _img_query_stmt = (
            sa.select(ImageRow)
            .join(ImageRow.registry_row)
            .options(load_only(ImageRow.id, ImageRow.labels, ImageRow.registry))
            .where(ContainerRegistryRow.is_global == true())
        )

        for row in await self.db_session.scalars(_img_query_stmt):
            image_row = cast(ImageRow, row)
            if not self._is_image_accessible_for_user(image_row, allowed_registries, scope.user_id):
                continue
            image_id_permission_map[image_row.id] = permissions

        return ImagePermissionContext(
            object_id_to_additional_permission_map=image_id_permission_map
        )

    async def _in_domain_scope(
        self,
        ctx: ClientContext,
        scope: DomainScope,
    ) -> ImagePermissionContext:
        from .container_registry import ContainerRegistryRow
        from .domain import DomainRow

        permissions = await self.calculate_permission(ctx, scope)
        image_id_permission_map: dict[UUID, frozenset[ImagePermission]] = {}

        _domain_query_stmt = sa.select(DomainRow).where(DomainRow.name == scope.domain_name)
        domain_row = cast(Optional[DomainRow], await self.db_session.scalar(_domain_query_stmt))
        if domain_row is None:
            raise InvalidScope(f"Domain not found (n:{scope.domain_name})")

        allowed_registries: set[str] = set(domain_row.allowed_docker_registries)

        _img_query_stmt = (
            sa.select(ImageRow)
            .join(ImageRow.registry_row)
            .options(load_only(ImageRow.id, ImageRow.registry))
            .where(ContainerRegistryRow.is_global == true())
        )

        for row in await self.db_session.scalars(_img_query_stmt):
            _row = cast(ImageRow, row)
            if _row.registry in allowed_registries:
                image_id_permission_map[_row.id] = permissions

        return ImagePermissionContext(
            object_id_to_additional_permission_map=image_id_permission_map
        )

    async def _get_user_accessible_project_scopes(
        self,
        ctx: ClientContext,
        scope: UserScope,
    ) -> list[ProjectScope]:
        from .group import AssocGroupUserRow

        get_assoc_group_ids_stmt = sa.select(AssocGroupUserRow.group_id).where(
            AssocGroupUserRow.user_id == scope.user_id
        )
        group_ids = await self.db_session.scalars(get_assoc_group_ids_stmt)

        return [ProjectScope(project_id=group_id) for group_id in group_ids]

    async def _get_domain_accessible_project_scopes(
        self,
        ctx: ClientContext,
        scope: DomainScope,
    ) -> list[ProjectScope]:
        from .group import GroupRow

        stmt = sa.select(GroupRow.id).where(GroupRow.domain_name == scope.domain_name)
        project_ids = await self.db_session.scalars(stmt)
        return [ProjectScope(project_id=proj_id) for proj_id in project_ids]

    async def _verify_project_scope_and_calculate_permission(
        self, ctx: ClientContext, scope: ProjectScope
    ) -> frozenset[ImagePermission]:
        from .group import GroupRow

        group_query_stmt = sa.select(GroupRow).where(GroupRow.id == scope.project_id)
        group_row = cast(Optional[GroupRow], await self.db_session.scalar(group_query_stmt))
        if group_row is None:
            raise InvalidScope(f"Project not found (project_id: {scope.project_id})")

        return await self.calculate_permission(ctx, scope)

    async def _in_project_scopes_by_registry_condition(
        self,
        ctx: ClientContext,
        scopes: list[ProjectScope],
        registry_condition_factory: Callable[[list[Any]], Any],
        filter_global_registry: bool = False,
        filter_customized_image: bool = False,
    ) -> ImagePermissionContext:
        from .container_registry import ContainerRegistryRow

        project_ids = [scope.project_id for scope in scopes]
        project_id_to_permission_map: dict[str, frozenset[ImagePermission]] = {}

        for scope in scopes:
            permissions = await self._verify_project_scope_and_calculate_permission(ctx, scope)
            project_id_to_permission_map[str(scope.project_id)] = permissions

        image_select_stmt = (
            sa.select(ImageRow)
            .join(ImageRow.registry_row)
            .options(
                joinedload(ImageRow.registry_row).joinedload(
                    ContainerRegistryRow.association_container_registries_groups_rows
                )
            )
            .where(registry_condition_factory(project_ids))
        )

        image_id_to_permission_map: dict[UUID, frozenset[ImagePermission]] = {}

        result = (await self.db_session.scalars(image_select_stmt)).unique()
        for row in result:
            img_row = cast(ImageRow, row)

            if filter_customized_image:
                allowed_registries = await self._get_allowed_registries_for_user(ctx, ctx.user_id)
                if not self._is_image_accessible_for_user(img_row, allowed_registries, ctx.user_id):
                    continue

            if filter_global_registry:
                # Assumption: permissions for global registry images is same across all projects.
                image_id_to_permission_map[img_row.id] = list(
                    project_id_to_permission_map.values()
                )[0]
            else:
                assoc_project_ids = [
                    assoc.group_id
                    for assoc in img_row.registry_row.association_container_registries_groups_rows
                ]
                for project_id in assoc_project_ids:
                    image_id_to_permission_map[img_row.id] = project_id_to_permission_map[
                        str(project_id)
                    ]

        return ImagePermissionContext(
            object_id_to_additional_permission_map=image_id_to_permission_map
        )

    async def _in_project_scopes_global(
        self,
        ctx: ClientContext,
        scopes: list[ProjectScope],
        filter_customized_image: bool = False,
    ) -> ImagePermissionContext:
        from .container_registry import ContainerRegistryRow

        def global_registry_condition(project_ids: list[Any]):
            return ContainerRegistryRow.is_global == true()

        return await self._in_project_scopes_by_registry_condition(
            ctx, scopes, global_registry_condition, True, filter_customized_image
        )

    async def _in_project_scopes_non_global(
        self,
        ctx: ClientContext,
        scopes: list[ProjectScope],
        filter_customized_image: bool = False,
    ) -> ImagePermissionContext:
        from .association_container_registries_groups import AssociationContainerRegistriesGroupsRow
        from .container_registry import ContainerRegistryRow

        def non_global_registry_condition(project_ids: list[Any]):
            return ContainerRegistryRow.association_container_registries_groups_rows.any(
                AssociationContainerRegistriesGroupsRow.group_id.in_(project_ids)
            )

        return await self._in_project_scopes_by_registry_condition(
            ctx, scopes, non_global_registry_condition, False, filter_customized_image
        )

    @override
    @classmethod
    async def _permission_for_owner(
        cls,
    ) -> frozenset[ImagePermission]:
        return OWNER_PERMISSIONS

    @override
    @classmethod
    async def _permission_for_admin(
        cls,
    ) -> frozenset[ImagePermission]:
        return ADMIN_PERMISSIONS

    @override
    @classmethod
    async def _permission_for_monitor(
        cls,
    ) -> frozenset[ImagePermission]:
        return MONITOR_PERMISSIONS

    @override
    @classmethod
    async def _permission_for_privileged_member(
        cls,
    ) -> frozenset[ImagePermission]:
        return PRIVILEGED_MEMBER_PERMISSIONS

    @override
    @classmethod
    async def _permission_for_member(
        cls,
    ) -> frozenset[ImagePermission]:
        return MEMBER_PERMISSIONS


async def get_permission_ctx(
    db_conn: AsyncConnection,
    ctx: ClientContext,
    target_scope: ScopeType,
    requested_permission: ImagePermission,
) -> ImagePermissionContext:
    async with ctx.db.begin_readonly_session(db_conn) as db_session:
        builder = ImagePermissionContextBuilder(db_session)
        permission_ctx = await builder.build(ctx, target_scope, requested_permission)
    return permission_ctx
