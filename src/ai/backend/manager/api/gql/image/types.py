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
class ImageV2AliasGQL(Node):
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
class ImageV2GQL(Node):
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
    name="ImageV2Scope",
    description=dedent_strip("""
    Added in 26.2.0.

    Scope for querying aliases within a specific image.
    """),
)
class ImageV2ScopeGQL:
    image_id: uuid.UUID = strawberry.field(description="UUID of the image to scope the query to.")


@strawberry.input(
    description=dedent_strip("""
    Added in 26.2.0.

    Filter options for images based on various criteria such as status,
    name, and architecture.

    Supports logical operations (AND, OR, NOT) for complex filtering scenarios.
    """)
)
class ImageV2FilterGQL(GQLFilter):
    status: list[ImageV2StatusGQL] | None = None
    name: StringFilter | None = None
    architecture: StringFilter | None = None

    AND: list[ImageV2FilterGQL] | None = None
    OR: list[ImageV2FilterGQL] | None = None
    NOT: list[ImageV2FilterGQL] | None = None

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
    name="ImageV2OrderField",
    description=dedent_strip("""
    Added in 26.2.0.

    Fields available for ordering image queries.
    """),
)
class ImageV2OrderFieldGQL(enum.Enum):
    NAME = "NAME"
    CREATED_AT = "CREATED_AT"


@strawberry.input(
    description=dedent_strip("""
    Added in 26.2.0.

    Specifies the field and direction for ordering images in queries.
    """)
)
class ImageV2OrderByGQL(GQLOrderBy):
    field: ImageV2OrderFieldGQL
    direction: OrderDirection = OrderDirection.ASC

    def to_query_order(self) -> QueryOrder:
        """Convert to repository QueryOrder."""
        ascending = self.direction == OrderDirection.ASC
        match self.field:
            case ImageV2OrderFieldGQL.NAME:
                return ImageOrders.name(ascending)
            case ImageV2OrderFieldGQL.CREATED_AT:
                return ImageOrders.created_at(ascending)


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


@strawberry.input(
    description=dedent_strip("""
    Added in 26.2.0.

    Filter options for image aliases.
    Supports filtering by alias string.
    """)
)
class ImageV2AliasFilterGQL(GQLFilter):
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
    name="ImageV2AliasOrderField",
    description=dedent_strip("""
    Added in 26.2.0.

    Fields available for ordering image alias queries.
    """),
)
class ImageV2AliasOrderFieldGQL(enum.Enum):
    ALIAS = "ALIAS"


@strawberry.input(
    description=dedent_strip("""
    Added in 26.2.0.

    Specifies the field and direction for ordering image aliases in queries.
    """)
)
class ImageV2AliasOrderByGQL(GQLOrderBy):
    field: ImageV2AliasOrderFieldGQL
    direction: OrderDirection = OrderDirection.ASC

    def to_query_order(self) -> QueryOrder:
        """Convert to repository QueryOrder."""
        ascending = self.direction == OrderDirection.ASC
        match self.field:
            case ImageV2AliasOrderFieldGQL.ALIAS:
                return ImageAliasOrders.alias(ascending)
