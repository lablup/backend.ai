from __future__ import annotations

import enum
from collections.abc import Sequence
from dataclasses import dataclass, field
from datetime import datetime
from decimal import Decimal
from functools import cached_property
from typing import Any, NamedTuple, override
from uuid import UUID

from ai.backend.common.data.entity.image_alias import ImageAliasID
from ai.backend.common.data.entity.types import EntityData, FieldData
from ai.backend.common.data.entity.user import UserID
from ai.backend.common.docker import ImageRef
from ai.backend.common.types import CIStrEnum, ImageCanonical, ImageID, SlotName
from ai.backend.common.utils import join_non_empty

type Resources = dict[SlotName, dict[str, Any]]


class ImageStatus(enum.StrEnum):
    ALIVE = "ALIVE"
    DELETED = "DELETED"
    PURGING = "PURGING"
    PURGE_ERROR = "PURGE_ERROR"

    @classmethod
    def purge_in_progress(cls) -> frozenset[ImageStatus]:
        """Statuses a purge is working through. Writes are refused while in one."""
        return frozenset({cls.PURGING, cls.PURGE_ERROR})

    @classmethod
    def restorable(cls) -> frozenset[ImageStatus]:
        """Statuses restore brings back to ALIVE: a forgotten image, or a live one left as is."""
        return frozenset({cls.ALIVE, cls.DELETED})


class ImageOrderField(enum.StrEnum):
    NAME = "NAME"
    CREATED_AT = "CREATED_AT"
    LAST_USED = "LAST_USED"


class ImageType(CIStrEnum):
    COMPUTE = "compute"
    SYSTEM = "system"
    SERVICE = "service"


class ImageIdentifier(NamedTuple):
    """
    Represent a tuple of image's canonical string and architecture, uniquely corresponding to an ImageRow.
    """

    canonical: str
    architecture: str


@dataclass
class ImageLabelsData:
    label_data: dict[str, str]


@dataclass
class ImageResourcesData:
    resources_data: Resources


@dataclass
class ImageTagEntry:
    """A single parsed tag component from the image reference."""

    key: str
    value: str


@dataclass
class ResourceLimit:
    key: str
    min: str
    max: str | None


@dataclass
class ImageData(EntityData):
    id: ImageID = field(compare=False)
    name: ImageCanonical
    project: str | None
    image: str
    created_at: datetime | None = field(compare=False)
    tag: str | None
    registry: str
    registry_id: UUID
    architecture: str
    config_digest: str
    size_bytes: int
    is_local: bool
    type: ImageType
    accelerators: str | None
    labels: ImageLabelsData
    resources: ImageResourcesData
    resource_limits: list[ResourceLimit]
    tags: list[ImageTagEntry]
    status: ImageStatus
    #: Whether a session commit made this image.
    customized: bool
    #: The user a customized image was committed for. ``None`` where the image is not
    #: customized, or where that user is gone.
    creator_id: UserID | None
    last_used_at: datetime | None = field(default=None, compare=False)

    @override
    def entity_id(self) -> ImageID:
        return self.id

    @cached_property
    def image_ref(self) -> ImageRef:
        if self.project == self.image:
            image_name = ""
            _, tag = ImageRef.parse_image_tag(self.name.split(f"{self.registry}/", maxsplit=1)[1])
        else:
            prefix = join_non_empty(self.registry, self.project, sep="/")
            image_name, tag = ImageRef.parse_image_tag(self.name.removeprefix(f"{prefix}/"))
        return ImageRef(
            image_name, self.project, tag, self.registry, self.architecture, self.is_local
        )

    def to_detailed(self, aliases: Sequence[str]) -> ImageDataWithDetails:
        version, ptag_set = self.image_ref.tag_set
        digest = self.config_digest.strip() or None
        return ImageDataWithDetails(
            id=self.id,
            name=ImageCanonical(self.image),
            namespace=self.image,
            base_image_name=self.image_ref.name,
            project=self.project or "",
            humanized_name=self.image,
            tag=self.tag,
            tags=[KVPair(key=k, value=v) for k, v in ptag_set.items()],
            version=version,
            registry=self.registry,
            registry_id=self.registry_id,
            type=self.type,
            architecture=self.architecture,
            is_local=self.is_local,
            digest=digest,
            labels=[
                KVPair(key=k, value=v) for k, v in self.labels.label_data.items() if v is not None
            ],
            aliases=list(aliases),
            size_bytes=self.size_bytes,
            status=self.status,
            resource_limits=[
                ResourceLimit(key=str(k), min=str(v.get("min", 0)), max=None)
                for k, v in self.resources.resources_data.items()
            ],
            supported_accelerators=self.accelerators.split(",") if self.accelerators else ["*"],
            customized=self.customized,
            creator_id=self.creator_id,
            created_at=self.created_at,
            last_used_at=self.last_used_at,
            hash=digest,
        )


@dataclass
class KVPair:
    key: str
    value: str


@dataclass
class ResourceLimitInput:
    """Input for setting a resource limit with optional min/max values."""

    slot_name: str
    min_value: Decimal | None
    max_value: Decimal | None


@dataclass
class ImageDataWithDetails:
    id: ImageID = field(compare=False)
    name: ImageCanonical
    namespace: str
    base_image_name: str
    project: str
    humanized_name: str
    tag: str | None
    tags: list[KVPair]
    version: str | None
    registry: str
    registry_id: UUID
    type: ImageType
    architecture: str
    is_local: bool
    status: ImageStatus
    resource_limits: list[ResourceLimit]
    #: Whether a session commit made this image.
    customized: bool
    #: The user a customized image was committed for. ``None`` where the image is not
    #: customized, or where that user is gone.
    creator_id: UserID | None
    supported_accelerators: list[str] = field(default_factory=list)
    digest: str | None = field(default=None)
    labels: list[KVPair] = field(default_factory=list)
    aliases: list[str] = field(default_factory=list)
    size_bytes: int = field(default=0)
    created_at: datetime | None = field(default=None)
    last_used_at: datetime | None = field(default=None, compare=False)
    # legacy
    hash: str | None = field(default=None)


@dataclass
class ImageAgentInstallStatus:
    """
    Represents the installation status of an image on agents.
    """

    installed: bool
    agent_names: list[str] = field(default_factory=list)


@dataclass
class ImageWithAgentInstallStatus:
    """
    Wraps detailed image information and its agent installation status.
    """

    image: ImageDataWithDetails
    agent_install_status: ImageAgentInstallStatus


@dataclass
class RescanImagesResult:
    images: list[ImageData]
    errors: list[str] = field(default_factory=list)


@dataclass
class ImageAliasData(FieldData):
    id: ImageAliasID = field(compare=False)
    alias: str


@dataclass
class ImageAliasListResult:
    """Search result with total count and pagination info for image aliases."""

    items: list[ImageAliasData]
    image_ids: list[ImageID]
    total_count: int
    has_next_page: bool
    has_previous_page: bool
