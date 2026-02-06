"""
ImageV2 GQL type definitions for Strawberry GraphQL.

This module implements ImageV2 types as specified in BEP-1038.
"""

from __future__ import annotations

import enum
import uuid
from datetime import datetime
from typing import Any, Self

import strawberry
from strawberry import Info
from strawberry.relay import Connection, Edge, Node, NodeID

from ai.backend.common.types import ImageID
from ai.backend.manager.api.gql.base import OrderDirection, StringFilter
from ai.backend.manager.api.gql.types import GQLFilter, GQLOrderBy, StrawberryGQLContext
from ai.backend.manager.api.gql.utils import dedent_strip
from ai.backend.manager.data.image.types import (
    ImageAliasData,
    ImageData,
    ImageDataWithDetails,
    ImageStatus,
    ResourceLimit,
)
from ai.backend.manager.models.rbac.permission_defs import ImagePermission
from ai.backend.manager.repositories.base import (
    QueryCondition,
    QueryOrder,
    combine_conditions_or,
    negate_conditions,
)
from ai.backend.manager.repositories.image.options import (
    ImageAliasConditions,
    ImageAliasOrders,
    ImageConditions,
    ImageOrders,
)

# =============================================================================
# Enums
# =============================================================================


@strawberry.enum(
    name="ImageStatus",
    description=dedent_strip("""
    Added in 26.2.0.

    Status of an image in the system.
    """),
)
class ImageStatusGQL(enum.Enum):
    ALIVE = "ALIVE"
    DELETED = "DELETED"

    @classmethod
    def from_data(cls, status: ImageStatus) -> ImageStatusGQL:
        return cls(status.value)


@strawberry.enum(
    name="ImagePermission",
    description=dedent_strip("""
    Added in 26.2.0.

    Permission types for image operations.
    """),
)
class ImagePermissionGQL(enum.Enum):
    READ_ATTRIBUTE = "READ_ATTRIBUTE"
    UPDATE_ATTRIBUTE = "UPDATE_ATTRIBUTE"
    CREATE_CONTAINER = "CREATE_CONTAINER"
    FORGET_IMAGE = "FORGET_IMAGE"

    @classmethod
    def from_data(cls, permission: ImagePermission) -> ImagePermissionGQL:
        return cls(permission.value)


# =============================================================================
# Sub-Info Types (Leaf)
# =============================================================================


@strawberry.type(
    name="ImageLabelEntry",
    description=dedent_strip("""
    Added in 26.2.0.

    A key-value pair representing a Docker label on the image.
    Labels contain metadata about the image such as maintainer, version, etc.
    """),
)
class ImageLabelEntryGQL:
    key: str = strawberry.field(description="The label key (e.g., 'maintainer').")
    value: str = strawberry.field(description="The label value.")

    @classmethod
    def from_dict_item(cls, key: str, value: str) -> Self:
        return cls(key=key, value=value)


@strawberry.type(
    name="ImageResourceLimit",
    description=dedent_strip("""
    Added in 26.2.0.

    Resource limit specification for an image.
    Defines minimum and maximum values for a resource slot.
    """),
)
class ImageResourceLimitGQL:
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
    name="ImageTagEntry",
    description=dedent_strip("""
    Added in 26.2.0.

    A key-value pair representing a parsed tag component.
    Tags are extracted from the image reference (e.g., py311, cuda12.1).
    """),
)
class ImageTagEntryGQL:
    key: str = strawberry.field(description="The tag key (e.g., 'python', 'cuda').")
    value: str = strawberry.field(description="The tag value (e.g., '3.11', '12.1').")

    @classmethod
    def from_dict_item(cls, key: str, value: str) -> Self:
        return cls(key=key, value=value)


@strawberry.type(
    name="ImageAlias",
    description=dedent_strip("""
    Added in 26.2.0.

    Represents an alias for a container image.
    Aliases provide alternative names for images.
    """),
)
class ImageAliasGQL(Node):
    id: NodeID[uuid.UUID]
    alias: str = strawberry.field(description="The alias string for the image.")

    @classmethod
    def from_data(cls, data: ImageAliasData) -> Self:
        return cls(id=data.id, alias=data.alias)


# =============================================================================
# Info Types (Grouped)
# =============================================================================


@strawberry.type(
    name="ImageIdentityInfo",
    description=dedent_strip("""
    Added in 26.2.0.

    Identity information for an image.
    Contains the canonical name, namespace, and architecture.
    """),
)
class ImageIdentityInfoGQL:
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
    name="ImageMetadataInfo",
    description=dedent_strip("""
    Added in 26.2.0.

    Metadata information for an image.
    Contains tags, labels, digest, size, status, and creation timestamp.
    """),
)
class ImageMetadataInfoGQL:
    tags: list[ImageTagEntryGQL] = strawberry.field(
        description="Parsed tag components from the image reference (e.g., python=3.11, cuda=12.1)."
    )
    labels: list[ImageLabelEntryGQL] = strawberry.field(description="Docker labels.")
    digest: str | None = strawberry.field(
        description="Config digest (image hash) for verification."
    )
    size_bytes: int = strawberry.field(description="Image size in bytes.")
    status: ImageStatusGQL = strawberry.field(description="Image status (ALIVE or DELETED).")
    created_at: datetime | None = strawberry.field(
        description="Timestamp when the image was created/registered."
    )

    @classmethod
    def from_data(cls, data: ImageData) -> Self:
        return cls(
            tags=[ImageTagEntryGQL.from_dict_item(entry.key, entry.value) for entry in data.tags],
            labels=[
                ImageLabelEntryGQL.from_dict_item(k, v) for k, v in data.labels.label_data.items()
            ],
            digest=data.config_digest,
            size_bytes=data.size_bytes,
            status=ImageStatusGQL.from_data(data.status),
            created_at=data.created_at,
        )

    @classmethod
    def from_detailed_data(cls, data: ImageDataWithDetails) -> Self:
        return cls(
            tags=[ImageTagEntryGQL.from_dict_item(kv.key, kv.value) for kv in data.tags],
            labels=[ImageLabelEntryGQL.from_dict_item(kv.key, kv.value) for kv in data.labels],
            digest=data.digest,
            size_bytes=data.size_bytes,
            status=ImageStatusGQL.from_data(data.status),
            created_at=data.created_at,
        )


@strawberry.type(
    name="ImageRequirementsInfo",
    description=dedent_strip("""
    Added in 26.2.0.

    Runtime requirements information for an image.
    Contains resource limits and supported accelerators.
    """),
)
class ImageRequirementsInfoGQL:
    resource_limits: list[ImageResourceLimitGQL] = strawberry.field(
        description="Resource slot limits (cpu, memory, accelerators, etc.)."
    )
    supported_accelerators: list[str] = strawberry.field(
        description="List of supported accelerator types (e.g., 'cuda', 'rocm')."
    )

    @classmethod
    def from_data(cls, data: ImageData) -> Self:
        accelerators = data.accelerators.split(",") if data.accelerators else []
        return cls(
            resource_limits=[ImageResourceLimitGQL.from_data(rl) for rl in data.resource_limits],
            supported_accelerators=[a.strip() for a in accelerators if a.strip()],
        )

    @classmethod
    def from_detailed_data(cls, data: ImageDataWithDetails) -> Self:
        return cls(
            resource_limits=[ImageResourceLimitGQL.from_data(rl) for rl in data.resource_limits],
            supported_accelerators=[a.strip() for a in data.supported_accelerators if a.strip()],
        )


@strawberry.type(
    name="ImagePermissionInfo",
    description=dedent_strip("""
    Added in 26.2.0.

    Permission information for an image.
    Contains the list of permissions the current user has on this image.
    """),
)
class ImagePermissionInfoGQL:
    permissions: list[ImagePermissionGQL] = strawberry.field(
        description="List of permissions the user has on this image."
    )

    @classmethod
    def from_permissions(cls, permissions: list[ImagePermission]) -> Self:
        return cls(permissions=[ImagePermissionGQL.from_data(p) for p in permissions])


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
class ImageV2GQL(Node):
    _image_id: strawberry.Private[ImageID]

    id: NodeID[uuid.UUID]

    # Sub-info types
    identity: ImageIdentityInfoGQL = strawberry.field(
        description="Image identity information (name, architecture)."
    )
    metadata: ImageMetadataInfoGQL = strawberry.field(
        description="Image metadata (labels, digest, size, status, created_at)."
    )
    requirements: ImageRequirementsInfoGQL = strawberry.field(
        description="Runtime requirements (supported_accelerators)."
    )
    permission: ImagePermissionInfoGQL | None = strawberry.field(
        default=None, description="Permission info for the current user. May be null."
    )

    # Registry (ContainerRegistryNode connection to be added later)
    registry_id: uuid.UUID = strawberry.field(
        description="UUID of the container registry where this image is stored."
    )

    @strawberry.field(description="Added in 26.2.0. Aliases for this image.")  # type: ignore[misc]
    async def aliases(
        self,
        info: Info[StrawberryGQLContext],
        filter: ImageAliasFilterGQL | None = None,
        order_by: list[ImageAliasOrderByGQL] | None = None,
        before: str | None = None,
        after: str | None = None,
        first: int | None = None,
        last: int | None = None,
    ) -> ImageAliasConnectionGQL:
        """Get the aliases for this image with pagination, filtering, and ordering."""
        from .fetcher import fetch_image_aliases

        base_conditions = [ImageAliasConditions.by_image_ids([self._image_id])]
        return await fetch_image_aliases(
            info,
            filter=filter,
            order_by=order_by,
            before=before,
            after=after,
            first=first,
            last=last,
            base_conditions=base_conditions,
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
            identity=ImageIdentityInfoGQL.from_data(data),
            metadata=ImageMetadataInfoGQL.from_data(data),
            requirements=ImageRequirementsInfoGQL.from_data(data),
            permission=ImagePermissionInfoGQL.from_permissions(permissions)
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
            identity=ImageIdentityInfoGQL.from_detailed_data(data),
            metadata=ImageMetadataInfoGQL.from_detailed_data(data),
            requirements=ImageRequirementsInfoGQL.from_detailed_data(data),
            permission=ImagePermissionInfoGQL.from_permissions(permissions)
            if permissions
            else None,
            registry_id=data.registry_id,
        )


# Edge type using strawberry.relay.Edge
ImageEdgeGQL = Edge[ImageV2GQL]


@strawberry.type(
    name="ImageConnectionV2",
    description=dedent_strip("""
    Added in 26.2.0.

    Relay-style connection for paginated image queries.
    Includes total count for pagination UI.
    """),
)
class ImageConnectionV2GQL(Connection[ImageV2GQL]):
    count: int = strawberry.field(description="Total count of images matching the query.")

    def __init__(self, *args: Any, count: int, **kwargs: Any) -> None:
        super().__init__(*args, **kwargs)
        self.count = count


# =============================================================================
# Filter and OrderBy Types
# =============================================================================


@strawberry.input(
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


@strawberry.input(
    name="ImageScope",
    description=dedent_strip("""
    Added in 26.2.0.

    Scope for querying aliases within a specific image.
    """),
)
class ImageScopeGQL:
    image_id: uuid.UUID = strawberry.field(description="UUID of the image to scope the query to.")


@strawberry.input(
    description=dedent_strip("""
    Added in 26.2.0.

    Filter options for images based on various criteria such as status,
    name, and architecture.

    Supports logical operations (AND, OR, NOT) for complex filtering scenarios.
    """)
)
class ImageFilterGQL(GQLFilter):
    status: list[ImageStatusGQL] | None = None
    name: StringFilter | None = None
    architecture: StringFilter | None = None

    AND: list[ImageFilterGQL] | None = None
    OR: list[ImageFilterGQL] | None = None
    NOT: list[ImageFilterGQL] | None = None

    def build_conditions(self) -> list[QueryCondition]:
        """Build query conditions from this filter.

        Returns a list containing QueryConditions that represent
        all filters with proper logical operators applied.
        """

        field_conditions: list[QueryCondition] = []

        # Apply status filter
        if self.status:
            statuses = [ImageStatus(s.value) for s in self.status]
            field_conditions.append(ImageConditions.by_statuses(statuses))

        # Apply name filter
        if self.name:
            name_condition = self.name.build_query_condition(
                contains_factory=ImageConditions.by_name_contains,
                equals_factory=ImageConditions.by_name_equals,
                starts_with_factory=ImageConditions.by_name_starts_with,
                ends_with_factory=ImageConditions.by_name_ends_with,
            )
            if name_condition:
                field_conditions.append(name_condition)

        # Apply architecture filter
        if self.architecture:
            arch_condition = self.architecture.build_query_condition(
                contains_factory=ImageConditions.by_architecture_contains,
                equals_factory=ImageConditions.by_architecture_equals,
                starts_with_factory=ImageConditions.by_architecture_starts_with,
                ends_with_factory=ImageConditions.by_architecture_ends_with,
            )
            if arch_condition:
                field_conditions.append(arch_condition)

        # Handle AND logical operator
        if self.AND:
            for sub_filter in self.AND:
                field_conditions.extend(sub_filter.build_conditions())

        # Handle OR logical operator
        if self.OR:
            or_sub_conditions: list[QueryCondition] = []
            for sub_filter in self.OR:
                or_sub_conditions.extend(sub_filter.build_conditions())
            if or_sub_conditions:
                field_conditions.append(combine_conditions_or(or_sub_conditions))

        # Handle NOT logical operator
        if self.NOT:
            not_sub_conditions: list[QueryCondition] = []
            for sub_filter in self.NOT:
                not_sub_conditions.extend(sub_filter.build_conditions())
            if not_sub_conditions:
                field_conditions.append(negate_conditions(not_sub_conditions))

        return field_conditions


@strawberry.enum(
    name="ImageOrderField",
    description=dedent_strip("""
    Added in 26.2.0.

    Fields available for ordering image queries.
    """),
)
class ImageOrderFieldGQL(enum.Enum):
    NAME = "NAME"
    CREATED_AT = "CREATED_AT"


@strawberry.input(
    description=dedent_strip("""
    Added in 26.2.0.

    Specifies the field and direction for ordering images in queries.
    """)
)
class ImageOrderByGQL(GQLOrderBy):
    field: ImageOrderFieldGQL
    direction: OrderDirection = OrderDirection.ASC

    def to_query_order(self) -> QueryOrder:
        """Convert to repository QueryOrder."""
        ascending = self.direction == OrderDirection.ASC
        match self.field:
            case ImageOrderFieldGQL.NAME:
                return ImageOrders.name(ascending)
            case ImageOrderFieldGQL.CREATED_AT:
                return ImageOrders.created_at(ascending)


# =============================================================================
# Image Alias Types
# =============================================================================

# Edge type using strawberry.relay.Edge
ImageAliasEdgeGQL = Edge[ImageAliasGQL]


@strawberry.type(
    name="ImageAliasConnection",
    description=dedent_strip("""
    Added in 26.2.0.

    Relay-style connection for paginated image alias queries.
    Includes total count for pagination UI.
    """),
)
class ImageAliasConnectionGQL(Connection[ImageAliasGQL]):
    count: int = strawberry.field(description="Total count of aliases matching the query.")

    def __init__(self, *args: Any, count: int, **kwargs: Any) -> None:
        super().__init__(*args, **kwargs)
        self.count = count


@strawberry.input(
    description=dedent_strip("""
    Added in 26.2.0.

    Filter options for image aliases.
    Supports filtering by alias string.
    """)
)
class ImageAliasFilterGQL(GQLFilter):
    alias: StringFilter | None = None

    def build_conditions(self) -> list[QueryCondition]:
        """Build query conditions from this filter."""
        field_conditions: list[QueryCondition] = []

        if self.alias:
            alias_condition = self.alias.build_query_condition(
                contains_factory=ImageAliasConditions.by_alias_contains,
                equals_factory=ImageAliasConditions.by_alias_equals,
                starts_with_factory=ImageAliasConditions.by_alias_starts_with,
                ends_with_factory=ImageAliasConditions.by_alias_ends_with,
            )
            if alias_condition:
                field_conditions.append(alias_condition)

        return field_conditions


@strawberry.enum(
    name="ImageAliasOrderField",
    description=dedent_strip("""
    Added in 26.2.0.

    Fields available for ordering image alias queries.
    """),
)
class ImageAliasOrderFieldGQL(enum.Enum):
    ALIAS = "ALIAS"


@strawberry.input(
    description=dedent_strip("""
    Added in 26.2.0.

    Specifies the field and direction for ordering image aliases in queries.
    """)
)
class ImageAliasOrderByGQL(GQLOrderBy):
    field: ImageAliasOrderFieldGQL
    direction: OrderDirection = OrderDirection.ASC

    def to_query_order(self) -> QueryOrder:
        """Convert to repository QueryOrder."""
        ascending = self.direction == OrderDirection.ASC
        match self.field:
            case ImageAliasOrderFieldGQL.ALIAS:
                return ImageAliasOrders.alias(ascending)
