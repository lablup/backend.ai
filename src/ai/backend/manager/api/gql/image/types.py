"""
ImageV2 GQL type definitions for Strawberry GraphQL.

This module implements ImageV2 types as specified in BEP-1038.
"""

from __future__ import annotations

import enum
import uuid
from collections.abc import Iterable
from datetime import datetime
from typing import Any, Self

import strawberry
from strawberry import Info
from strawberry.relay import Connection, Edge, NodeID

from ai.backend.common.dto.manager.v2.image.request import (
    AdminSearchImageAliasesInput,
    ContainerRegistryScopeInputDTO,
    ImageAliasFilterInputDTO,
    ImageAliasNestedFilterInputDTO,
    ImageAliasOrderByInputDTO,
    ImageFilterInputDTO,
    ImageOrderByInputDTO,
    ImageScopeInputDTO,
    ImageStatusFilterInputDTO,
)
from ai.backend.common.dto.manager.v2.image.response import ImageAliasNode, ImageNode
from ai.backend.common.dto.manager.v2.image.types import (
    ImageOrderField as ImageOrderFieldDTO,
)
from ai.backend.common.dto.manager.v2.image.types import (
    ImageStatusType,
)
from ai.backend.common.dto.manager.v2.image.types import (
    OrderDirection as OrderDirectionDTO,
)
from ai.backend.common.types import ImageID
from ai.backend.manager.api.gql.base import (
    DateTimeFilter,
    OrderDirection,
    StringFilter,
    UUIDFilter,
    encode_cursor,
)
from ai.backend.manager.api.gql.pydantic_compat import PydanticNodeMixin
from ai.backend.manager.api.gql.types import GQLFilter, GQLOrderBy, StrawberryGQLContext
from ai.backend.manager.api.gql.utils import dedent_strip
from ai.backend.manager.data.image.types import (
    ImageAliasData,
    ImageData,
    ImageDataWithDetails,
    ImageStatus,
    ResourceLimit,
)
from ai.backend.manager.models.image.conditions import ImageAliasConditions
from ai.backend.manager.models.rbac.permission_defs import ImagePermission

# =============================================================================
# Enums
# =============================================================================


@strawberry.enum(
    name="ImageV2Status",
    description=dedent_strip("""
    Added in 26.2.0.

    Status of an image in the system.
    """),
)
class ImageV2StatusGQL(enum.Enum):
    ALIVE = "ALIVE"
    DELETED = "DELETED"

    @classmethod
    def from_data(cls, status: ImageStatus) -> ImageV2StatusGQL:
        return cls(status.value)


@strawberry.enum(
    name="ImageV2Permission",
    description=dedent_strip("""
    Added in 26.2.0.

    Permission types for image operations.
    """),
)
class ImageV2PermissionGQL(enum.Enum):
    READ_ATTRIBUTE = "READ_ATTRIBUTE"
    UPDATE_ATTRIBUTE = "UPDATE_ATTRIBUTE"
    CREATE_CONTAINER = "CREATE_CONTAINER"
    FORGET_IMAGE = "FORGET_IMAGE"

    @classmethod
    def from_data(cls, permission: ImagePermission) -> ImageV2PermissionGQL:
        return cls(permission.value)


# =============================================================================
# Sub-Info Types (Leaf)
# =============================================================================


@strawberry.type(
    name="ImageV2LabelEntry",
    description=dedent_strip("""
    Added in 26.2.0.

    A key-value pair representing a Docker label on the image.
    Labels contain metadata about the image such as maintainer, version, etc.
    """),
)
class ImageV2LabelEntryGQL:
    key: str = strawberry.field(description="The label key (e.g., 'maintainer').")
    value: str = strawberry.field(description="The label value.")

    @classmethod
    def from_dict_item(cls, key: str, value: str) -> Self:
        return cls(key=key, value=value)


@strawberry.type(
    name="ImageV2ResourceLimit",
    description=dedent_strip("""
    Added in 26.2.0.

    Resource limit specification for an image.
    Defines minimum and maximum values for a resource slot.
    """),
)
class ImageV2ResourceLimitGQL:
    key: str = strawberry.field(
        description="Resource slot name (e.g., 'cpu', 'mem', 'cuda.shares')."
    )
    min: str = strawberry.field(description="Minimum required amount.")
    max: str = strawberry.field(description="Maximum allowed amount.")

    @classmethod
    def from_data(cls, data: ResourceLimit) -> Self:
        return cls(
            key=data.key,
            min=str(data.min),
            max=str(data.max),
        )


@strawberry.type(
    name="ImageV2TagEntry",
    description=dedent_strip("""
    Added in 26.2.0.

    A key-value pair representing a parsed tag component.
    Tags are extracted from the image reference (e.g., py311, cuda12.1).
    """),
)
class ImageV2TagEntryGQL:
    key: str = strawberry.field(description="The tag key (e.g., 'python', 'cuda').")
    value: str = strawberry.field(description="The tag value (e.g., '3.11', '12.1').")

    @classmethod
    def from_dict_item(cls, key: str, value: str) -> Self:
        return cls(key=key, value=value)


@strawberry.type(
    name="ImageV2Alias",
    description=dedent_strip("""
    Added in 26.2.0.

    Represents an alias for a container image.
    Aliases provide alternative names for images.
    """),
)
class ImageV2AliasGQL(PydanticNodeMixin):
    id: NodeID[uuid.UUID]
    alias: str = strawberry.field(description="The alias string for the image.")

    @classmethod
    async def resolve_nodes(  # type: ignore[override]  # Strawberry Node uses AwaitableOrValue overloads incompatible with async def
        cls,
        *,
        info: Info[StrawberryGQLContext],
        node_ids: Iterable[str],
        required: bool = False,
    ) -> Iterable[Self | None]:
        results = await info.context.data_loaders.image_alias_loader.load_many([
            uuid.UUID(nid) for nid in node_ids
        ])
        return [cls.from_data(data) if data is not None else None for data in results]

    @classmethod
    def from_data(cls, data: ImageAliasData) -> Self:
        return cls(id=data.id, alias=data.alias)

    @classmethod
    def from_node(cls, node: ImageAliasNode) -> Self:
        """Create ImageV2AliasGQL from ImageAliasNode DTO."""
        return cls(id=node.id, alias=node.alias)


# =============================================================================
# Info Types (Grouped)
# =============================================================================


@strawberry.type(
    name="ImageV2IdentityInfo",
    description=dedent_strip("""
    Added in 26.2.0.

    Identity information for an image.
    Contains the canonical name, namespace, and architecture.
    """),
)
class ImageV2IdentityInfoGQL:
    canonical_name: str = strawberry.field(
        description="Full canonical name (e.g., 'cr.backend.ai/stable/python:3.9')."
    )
    namespace: str = strawberry.field(
        description="Image namespace/path within the registry (e.g., 'stable/python')."
    )
    architecture: str = strawberry.field(
        description="CPU architecture (e.g., 'x86_64', 'aarch64')."
    )

    @classmethod
    def from_data(cls, data: ImageData) -> Self:
        return cls(
            canonical_name=str(data.name),
            namespace=data.image,
            architecture=data.architecture,
        )

    @classmethod
    def from_detailed_data(cls, data: ImageDataWithDetails) -> Self:
        return cls(
            canonical_name=str(data.name),
            namespace=data.namespace,
            architecture=data.architecture,
        )


@strawberry.type(
    name="ImageV2MetadataInfo",
    description=dedent_strip("""
    Added in 26.2.0.

    Metadata information for an image.
    Contains tags, labels, digest, size, status, and creation timestamp.
    """),
)
class ImageV2MetadataInfoGQL:
    tags: list[ImageV2TagEntryGQL] = strawberry.field(
        description="Parsed tag components from the image reference (e.g., python=3.11, cuda=12.1)."
    )
    labels: list[ImageV2LabelEntryGQL] = strawberry.field(description="Docker labels.")
    digest: str | None = strawberry.field(
        description="Config digest (image hash) for verification."
    )
    size_bytes: int = strawberry.field(description="Image size in bytes.")
    status: ImageV2StatusGQL = strawberry.field(description="Image status (ALIVE or DELETED).")
    created_at: datetime | None = strawberry.field(
        description="Timestamp when the image was created/registered."
    )

    @classmethod
    def from_data(cls, data: ImageData) -> Self:
        return cls(
            tags=[ImageV2TagEntryGQL.from_dict_item(entry.key, entry.value) for entry in data.tags],
            labels=[
                ImageV2LabelEntryGQL.from_dict_item(k, v) for k, v in data.labels.label_data.items()
            ],
            digest=data.config_digest,
            size_bytes=data.size_bytes,
            status=ImageV2StatusGQL.from_data(data.status),
            created_at=data.created_at,
        )

    @classmethod
    def from_detailed_data(cls, data: ImageDataWithDetails) -> Self:
        return cls(
            tags=[ImageV2TagEntryGQL.from_dict_item(kv.key, kv.value) for kv in data.tags],
            labels=[ImageV2LabelEntryGQL.from_dict_item(kv.key, kv.value) for kv in data.labels],
            digest=data.digest,
            size_bytes=data.size_bytes,
            status=ImageV2StatusGQL.from_data(data.status),
            created_at=data.created_at,
        )


@strawberry.type(
    name="ImageV2RequirementsInfo",
    description=dedent_strip("""
    Added in 26.2.0.

    Runtime requirements information for an image.
    Contains resource limits and supported accelerators.
    """),
)
class ImageV2RequirementsInfoGQL:
    resource_limits: list[ImageV2ResourceLimitGQL] = strawberry.field(
        description="Resource slot limits (cpu, memory, accelerators, etc.)."
    )
    supported_accelerators: list[str] = strawberry.field(
        description="List of supported accelerator types (e.g., 'cuda', 'rocm')."
    )

    @classmethod
    def from_data(cls, data: ImageData) -> Self:
        accelerators = data.accelerators.split(",") if data.accelerators else []
        return cls(
            resource_limits=[ImageV2ResourceLimitGQL.from_data(rl) for rl in data.resource_limits],
            supported_accelerators=[a.strip() for a in accelerators if a.strip()],
        )

    @classmethod
    def from_detailed_data(cls, data: ImageDataWithDetails) -> Self:
        return cls(
            resource_limits=[ImageV2ResourceLimitGQL.from_data(rl) for rl in data.resource_limits],
            supported_accelerators=[a.strip() for a in data.supported_accelerators if a.strip()],
        )


@strawberry.type(
    name="ImageV2PermissionInfo",
    description=dedent_strip("""
    Added in 26.2.0.

    Permission information for an image.
    Contains the list of permissions the current user has on this image.
    """),
)
class ImageV2PermissionInfoGQL:
    permissions: list[ImageV2PermissionGQL] = strawberry.field(
        description="List of permissions the user has on this image."
    )

    @classmethod
    def from_permissions(cls, permissions: list[ImagePermission]) -> Self:
        return cls(permissions=[ImageV2PermissionGQL.from_data(p) for p in permissions])


# =============================================================================
# Main Types
# =============================================================================


@strawberry.type(
    name="ImageV2",
    description=dedent_strip("""
    Added in 26.2.0.

    Represents a container image in Backend.AI.

    Images are container specifications that define the runtime environment
    for compute sessions. Each image has identity information, metadata,
    resource requirements, and permission settings.

    This is the V2 implementation using Strawberry GraphQL with Relay-style
    connections as part of BEP-1010 migration.
    """),
)
class ImageV2GQL(PydanticNodeMixin):
    _image_id: strawberry.Private[ImageID]

    id: NodeID[uuid.UUID]

    # Sub-info types
    identity: ImageV2IdentityInfoGQL = strawberry.field(
        description="Image identity information (name, architecture)."
    )
    metadata: ImageV2MetadataInfoGQL = strawberry.field(
        description="Image metadata (labels, digest, size, status, created_at)."
    )
    requirements: ImageV2RequirementsInfoGQL = strawberry.field(
        description="Runtime requirements (supported_accelerators)."
    )
    permission: ImageV2PermissionInfoGQL | None = strawberry.field(
        default=None, description="Permission info for the current user. May be null."
    )

    # Registry (ContainerRegistryNode connection to be added later)
    registry_id: uuid.UUID = strawberry.field(
        description="UUID of the container registry where this image is stored."
    )

    @strawberry.field(  # type: ignore[misc]
        description="Added in 26.3.0. Timestamp of the most recent session created with this image. Returns null if the image has never been used.",
    )
    async def last_used(self, info: Info[StrawberryGQLContext]) -> datetime | None:
        """Get the timestamp of the most recent session created with this image."""
        return await info.context.data_loaders.image_last_used_loader.load(self._image_id)

    @strawberry.field(description="Added in 26.2.0. Aliases for this image.")  # type: ignore[misc]
    async def aliases(
        self,
        info: Info[StrawberryGQLContext],
        filter: ImageV2AliasFilterGQL | None = None,
        order_by: list[ImageV2AliasOrderByGQL] | None = None,
        before: str | None = None,
        after: str | None = None,
        first: int | None = None,
        last: int | None = None,
    ) -> ImageV2AliasConnectionGQL:
        """Get the aliases for this image with pagination, filtering, and ordering."""
        pydantic_filter = filter.to_pydantic() if filter else None
        pydantic_orders = [o.to_pydantic() for o in order_by] if order_by else None
        base_conditions = [ImageAliasConditions.by_image_ids([self._image_id])]
        payload = await info.context.adapters.image.admin_search_image_aliases(
            AdminSearchImageAliasesInput(
                filter=pydantic_filter,
                order=pydantic_orders,
                first=first,
                after=after,
                last=last,
                before=before,
            ),
            base_conditions=base_conditions,
        )
        edges = [
            ImageV2AliasEdgeGQL(
                node=ImageV2AliasGQL.from_node(node),
                cursor=encode_cursor(node.id),
            )
            for node in payload.items
        ]
        page_info = strawberry.relay.PageInfo(
            has_next_page=payload.has_next_page,
            has_previous_page=payload.has_previous_page,
            start_cursor=edges[0].cursor if edges else None,
            end_cursor=edges[-1].cursor if edges else None,
        )
        return ImageV2AliasConnectionGQL(
            count=payload.total_count, edges=edges, page_info=page_info
        )

    @classmethod
    async def resolve_nodes(  # type: ignore[override]  # Strawberry Node uses AwaitableOrValue overloads incompatible with async def
        cls,
        *,
        info: Info[StrawberryGQLContext],
        node_ids: Iterable[str],
        required: bool = False,
    ) -> Iterable[Self | None]:
        results = await info.context.data_loaders.image_loader.load_many([
            ImageID(uuid.UUID(nid)) for nid in node_ids
        ])
        return [cls.from_data(data) if data is not None else None for data in results]

    @classmethod
    def from_node(cls, node: ImageNode) -> Self:
        """Create ImageV2GQL from ImageNode DTO.

        Args:
            node: The image node DTO from the adapter layer.

        Returns:
            ImageV2GQL instance.
        """
        accelerators = node.accelerators.split(",") if node.accelerators else []
        image_id = ImageID(node.id)
        return cls(
            id=node.id,
            _image_id=image_id,
            identity=ImageV2IdentityInfoGQL(
                canonical_name=node.name,
                namespace=node.image,
                architecture=node.architecture,
            ),
            metadata=ImageV2MetadataInfoGQL(
                tags=[ImageV2TagEntryGQL(key=t.key, value=t.value) for t in node.tags],
                labels=[ImageV2LabelEntryGQL(key=lb.key, value=lb.value) for lb in node.labels],
                digest=node.config_digest,
                size_bytes=node.size_bytes,
                status=ImageV2StatusGQL(node.status.value),
                created_at=node.created_at,
            ),
            requirements=ImageV2RequirementsInfoGQL(
                resource_limits=[
                    ImageV2ResourceLimitGQL(
                        key=rl.key,
                        min=str(rl.min),
                        max=str(rl.max) if rl.max is not None else "Infinity",
                    )
                    for rl in node.resource_limits
                ],
                supported_accelerators=[a.strip() for a in accelerators if a.strip()],
            ),
            permission=None,
            registry_id=node.registry_id,
        )

    @classmethod
    def from_data(
        cls,
        data: ImageData,
        permissions: list[ImagePermission] | None = None,
    ) -> Self:
        """Create ImageV2GQL from ImageData.

        Args:
            data: The image data.
            permissions: Optional list of permissions the user has on this image.

        Returns:
            ImageV2GQL instance.
        """
        return cls(
            id=data.id,
            _image_id=data.id,
            identity=ImageV2IdentityInfoGQL.from_data(data),
            metadata=ImageV2MetadataInfoGQL.from_data(data),
            requirements=ImageV2RequirementsInfoGQL.from_data(data),
            permission=ImageV2PermissionInfoGQL.from_permissions(permissions)
            if permissions
            else None,
            registry_id=data.registry_id,
        )

    @classmethod
    def from_detailed_data(
        cls,
        data: ImageDataWithDetails,
        permissions: list[ImagePermission] | None = None,
    ) -> Self:
        """Create ImageV2GQL from ImageDataWithDetails.

        Args:
            data: The detailed image data.
            permissions: Optional list of permissions the user has on this image.

        Returns:
            ImageV2GQL instance.
        """
        return cls(
            id=data.id,
            _image_id=data.id,
            identity=ImageV2IdentityInfoGQL.from_detailed_data(data),
            metadata=ImageV2MetadataInfoGQL.from_detailed_data(data),
            requirements=ImageV2RequirementsInfoGQL.from_detailed_data(data),
            permission=ImageV2PermissionInfoGQL.from_permissions(permissions)
            if permissions
            else None,
            registry_id=data.registry_id,
        )


# Edge type using strawberry.relay.Edge
ImageV2EdgeGQL = Edge[ImageV2GQL]


@strawberry.type(
    name="ImageV2Connection",
    description=dedent_strip("""
    Added in 26.2.0.

    Relay-style connection for paginated image queries.
    Includes total count for pagination UI.
    """),
)
class ImageV2ConnectionGQL(Connection[ImageV2GQL]):
    count: int = strawberry.field(description="Total count of images matching the query.")

    def __init__(self, *args: Any, count: int, **kwargs: Any) -> None:
        super().__init__(*args, **kwargs)
        self.count = count


# =============================================================================
# Filter and OrderBy Types
# =============================================================================


@strawberry.experimental.pydantic.input(
    model=ContainerRegistryScopeInputDTO,
    name="ContainerRegistryScope",
    description=dedent_strip("""
    Added in 26.2.0.

    Scope for querying images within a specific container registry.
    """),
)
class ContainerRegistryScopeGQL:
    registry_id: uuid.UUID = strawberry.field(
        description="UUID of the container registry to scope the query to."
    )

    def to_pydantic(self) -> ContainerRegistryScopeInputDTO:
        """Convert to pydantic DTO for adapter layer processing."""
        return ContainerRegistryScopeInputDTO(registry_id=self.registry_id)


@strawberry.experimental.pydantic.input(
    model=ImageScopeInputDTO,
    name="ImageV2Scope",
    description=dedent_strip("""
    Added in 26.2.0.

    Scope for querying aliases within a specific image.
    """),
)
class ImageV2ScopeGQL:
    image_id: uuid.UUID = strawberry.field(description="UUID of the image to scope the query to.")

    def to_pydantic(self) -> ImageScopeInputDTO:
        """Convert to pydantic DTO for adapter layer processing."""
        return ImageScopeInputDTO(image_id=self.image_id)


@strawberry.experimental.pydantic.input(
    model=ImageAliasNestedFilterInputDTO,
    name="ImageAliasNestedFilter",
    description=(
        "Added in 26.3.0. Nested filter for aliases belonging to an image. "
        "Filters images that have at least one alias matching all specified conditions."
    ),
)
class ImageAliasNestedFilterGQL:
    """Nested filter for image aliases within an image."""

    alias: StringFilter | None = strawberry.field(
        default=None,
        description="Filter by alias string. Supports equals, contains, startsWith, and endsWith.",
    )

    def to_pydantic(self) -> ImageAliasNestedFilterInputDTO:
        """Convert to pydantic DTO for adapter layer processing."""
        return ImageAliasNestedFilterInputDTO(
            alias=self.alias.to_pydantic() if self.alias else None,
        )


@strawberry.experimental.pydantic.input(
    model=ImageStatusFilterInputDTO,
    name="ImageV2StatusFilter",
    description="Added in 26.3.0. Filter for image status with equality and membership operators.",
)
class ImageV2StatusFilterGQL:
    equals: ImageV2StatusGQL | None = strawberry.field(
        default=None, description="Matches images with this exact status."
    )
    in_: list[ImageV2StatusGQL] | None = strawberry.field(
        name="in", default=None, description="Matches images whose status is in this list."
    )
    not_equals: ImageV2StatusGQL | None = strawberry.field(
        default=None, description="Excludes images with this exact status."
    )
    not_in: list[ImageV2StatusGQL] | None = strawberry.field(
        default=None, description="Excludes images whose status is in this list."
    )

    def to_pydantic(self) -> ImageStatusFilterInputDTO:
        """Convert to pydantic DTO for adapter layer processing."""
        return ImageStatusFilterInputDTO(
            equals=ImageStatusType(self.equals.value) if self.equals else None,
            in_=[ImageStatusType(s.value) for s in self.in_] if self.in_ else None,
            not_equals=ImageStatusType(self.not_equals.value) if self.not_equals else None,
            not_in=[ImageStatusType(s.value) for s in self.not_in] if self.not_in else None,
        )


@strawberry.experimental.pydantic.input(
    model=ImageFilterInputDTO,
    description=dedent_strip("""
    Added in 26.2.0.

    Filter options for images based on various criteria such as status,
    name, and architecture.

    Supports logical operations (AND, OR, NOT) for complex filtering scenarios.
    """),
)
class ImageV2FilterGQL(GQLFilter):
    status: ImageV2StatusFilterGQL | None = None
    name: StringFilter | None = None
    architecture: StringFilter | None = None
    registry_id: UUIDFilter | None = strawberry.field(
        default=None,
        description="Added in 26.4.0. Filter by container registry ID.",
    )
    alias: ImageAliasNestedFilterGQL | None = strawberry.field(
        default=None,
        description="Added in 26.3.0. Filter by nested alias conditions.",
    )
    last_used: DateTimeFilter | None = strawberry.field(
        default=None,
        description="Added in 26.3.0. Filter by last used datetime (before/after).",
    )
    AND: list[ImageV2FilterGQL] | None = None
    OR: list[ImageV2FilterGQL] | None = None
    NOT: list[ImageV2FilterGQL] | None = None

    def to_pydantic(self) -> ImageFilterInputDTO:
        """Convert to pydantic DTO for adapter layer processing."""
        return ImageFilterInputDTO(
            status=self.status.to_pydantic() if self.status else None,
            name=self.name.to_pydantic() if self.name else None,
            architecture=self.architecture.to_pydantic() if self.architecture else None,
            registry_id=self.registry_id.to_pydantic() if self.registry_id else None,
            alias=self.alias.to_pydantic() if self.alias else None,
            last_used=self.last_used.to_pydantic() if self.last_used else None,
            AND=[f.to_pydantic() for f in self.AND] if self.AND else None,
            OR=[f.to_pydantic() for f in self.OR] if self.OR else None,
            NOT=[f.to_pydantic() for f in self.NOT] if self.NOT else None,
        )


@strawberry.enum(
    name="ImageV2OrderField",
    description=dedent_strip("""
    Added in 26.2.0.

    Fields available for ordering image queries.
    """),
)
class ImageV2OrderFieldGQL(enum.Enum):
    NAME = "NAME"
    CREATED_AT = "CREATED_AT"
    LAST_USED = "LAST_USED"


@strawberry.experimental.pydantic.input(
    model=ImageOrderByInputDTO,
    description=dedent_strip("""
    Added in 26.2.0.

    Specifies the field and direction for ordering images in queries.
    """),
)
class ImageV2OrderByGQL(GQLOrderBy):
    field: ImageV2OrderFieldGQL
    direction: OrderDirection = OrderDirection.ASC

    def to_pydantic(self) -> ImageOrderByInputDTO:
        """Convert to pydantic DTO for adapter layer processing."""
        return ImageOrderByInputDTO(
            field=ImageOrderFieldDTO(self.field.value.lower()),
            direction=OrderDirectionDTO(self.direction.value.lower()),
        )


# =============================================================================
# Image Alias Types
# =============================================================================

# Edge type using strawberry.relay.Edge
ImageV2AliasEdgeGQL = Edge[ImageV2AliasGQL]


@strawberry.type(
    name="ImageV2AliasConnection",
    description=dedent_strip("""
    Added in 26.2.0.

    Relay-style connection for paginated image alias queries.
    Includes total count for pagination UI.
    """),
)
class ImageV2AliasConnectionGQL(Connection[ImageV2AliasGQL]):
    count: int = strawberry.field(description="Total count of aliases matching the query.")

    def __init__(self, *args: Any, count: int, **kwargs: Any) -> None:
        super().__init__(*args, **kwargs)
        self.count = count


@strawberry.experimental.pydantic.input(
    model=ImageAliasFilterInputDTO,
    description=dedent_strip("""
    Added in 26.2.0.

    Filter options for image aliases.
    Supports filtering by alias string and image ID.
    """),
)
class ImageV2AliasFilterGQL(GQLFilter):
    alias: StringFilter | None = None
    image_id: UUIDFilter | None = strawberry.field(
        default=None,
        description="Added in 26.4.0. Filter by image ID.",
    )

    AND: list[ImageV2AliasFilterGQL] | None = None
    OR: list[ImageV2AliasFilterGQL] | None = None
    NOT: list[ImageV2AliasFilterGQL] | None = None

    def to_pydantic(self) -> ImageAliasFilterInputDTO:
        """Convert to pydantic DTO for adapter layer processing."""
        return ImageAliasFilterInputDTO(
            alias=self.alias.to_pydantic() if self.alias else None,
            image_id=self.image_id.to_pydantic() if self.image_id else None,
            AND=[f.to_pydantic() for f in self.AND] if self.AND else None,
            OR=[f.to_pydantic() for f in self.OR] if self.OR else None,
            NOT=[f.to_pydantic() for f in self.NOT] if self.NOT else None,
        )


@strawberry.enum(
    name="ImageV2AliasOrderField",
    description=dedent_strip("""
    Added in 26.2.0.

    Fields available for ordering image alias queries.
    """),
)
class ImageV2AliasOrderFieldGQL(enum.Enum):
    ALIAS = "ALIAS"


@strawberry.experimental.pydantic.input(
    model=ImageAliasOrderByInputDTO,
    description=dedent_strip("""
    Added in 26.2.0.

    Specifies the field and direction for ordering image aliases in queries.
    """),
)
class ImageV2AliasOrderByGQL(GQLOrderBy):
    field: ImageV2AliasOrderFieldGQL
    direction: OrderDirection = OrderDirection.ASC

    def to_pydantic(self) -> ImageAliasOrderByInputDTO:
        """Convert to pydantic DTO for adapter layer processing."""
        return ImageAliasOrderByInputDTO(
            field=self.field.value.lower(),
            direction=OrderDirectionDTO(self.direction.value.lower()),
        )
