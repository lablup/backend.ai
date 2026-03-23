"""
ImageV2 GQL type definitions for Strawberry GraphQL.

This module implements ImageV2 types as specified in BEP-1038.
"""

from __future__ import annotations

import enum
import uuid
from collections.abc import Iterable
from datetime import datetime
from enum import StrEnum
from typing import Any, Self, cast

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
from ai.backend.common.dto.manager.v2.image.response import (
    ImageAliasNode,
    ImageIdentityInfoDTO,
    ImageMetadataInfoDTO,
    ImageNode,
    ImagePermissionInfoDTO,
    ImageRequirementsInfoDTO,
)
from ai.backend.common.dto.manager.v2.image.types import (
    ImageLabelInfo,
    ImageResourceLimitGQLInfo,
    ImageTagInfo,
)
from ai.backend.common.types import ImageID
from ai.backend.manager.api.gql.base import (
    DateTimeFilter,
    OrderDirection,
    StringFilter,
    UUIDFilter,
    encode_cursor,
)
from ai.backend.manager.api.gql.decorators import (
    BackendAIGQLMeta,
    gql_connection_type,
    gql_node_type,
    gql_pydantic_input,
    gql_pydantic_type,
)
from ai.backend.manager.api.gql.pydantic_compat import (
    PydanticInputMixin,
    PydanticNodeMixin,
    PydanticOutputMixin,
)
from ai.backend.manager.api.gql.types import GQLFilter, GQLOrderBy, StrawberryGQLContext
from ai.backend.manager.api.gql.utils import dedent_strip
from ai.backend.manager.models.image.conditions import ImageAliasConditions

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


# =============================================================================
# Sub-Info Types (Leaf)
# =============================================================================


@gql_pydantic_type(
    BackendAIGQLMeta(
        added_version="26.2.0",
        description="A key-value pair representing a Docker label on the image. Labels contain metadata about the image such as maintainer, version, etc.",
    ),
    model=ImageLabelInfo,
    name="ImageV2LabelEntry",
)
class ImageV2LabelEntryGQL:
    key: strawberry.auto
    value: strawberry.auto


@gql_pydantic_type(
    BackendAIGQLMeta(
        added_version="26.2.0",
        description="Resource limit specification for an image. Defines minimum and maximum values for a resource slot.",
    ),
    model=ImageResourceLimitGQLInfo,
    name="ImageV2ResourceLimit",
)
class ImageV2ResourceLimitGQL:
    key: strawberry.auto
    min: strawberry.auto
    max: strawberry.auto


@gql_pydantic_type(
    BackendAIGQLMeta(
        added_version="26.2.0",
        description="A key-value pair representing a parsed tag component. Tags are extracted from the image reference (e.g., py311, cuda12.1).",
    ),
    model=ImageTagInfo,
    name="ImageV2TagEntry",
)
class ImageV2TagEntryGQL:
    key: strawberry.auto
    value: strawberry.auto


@gql_node_type(
    BackendAIGQLMeta(
        added_version="26.2.0",
        description="Represents an alias for a container image. Aliases provide alternative names for images.",
    ),
    name="ImageV2Alias",
)
class ImageV2AliasGQL(PydanticNodeMixin[ImageAliasNode]):
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
        return cast(list[Self | None], results)


# =============================================================================
# Info Types (Grouped)
# =============================================================================


@gql_pydantic_type(
    BackendAIGQLMeta(
        added_version="26.2.0",
        description="Identity information for an image. Contains the canonical name, namespace, and architecture.",
    ),
    model=ImageIdentityInfoDTO,
    name="ImageV2IdentityInfo",
)
class ImageV2IdentityInfoGQL:
    canonical_name: strawberry.auto
    namespace: strawberry.auto
    architecture: strawberry.auto


@gql_pydantic_type(
    BackendAIGQLMeta(
        added_version="26.2.0",
        description="Metadata information for an image. Contains tags, labels, digest, size, status, and creation timestamp.",
    ),
    model=ImageMetadataInfoDTO,
    name="ImageV2MetadataInfo",
)
class ImageV2MetadataInfoGQL:
    digest: str | None = strawberry.field(
        description="Config digest (image hash) for verification."
    )
    size_bytes: int = strawberry.field(description="Image size in bytes.")
    created_at: datetime | None = strawberry.field(
        description="Timestamp when the image was created/registered."
    )
    last_used_at: datetime | None = strawberry.field(
        description="Added in 26.3.0. Timestamp of the most recent session created with this image. Returns null if the image has never been used.",
    )
    tags: list[ImageV2TagEntryGQL] = strawberry.field(
        description="Parsed tag components from the image reference (e.g., python=3.11, cuda=12.1)."
    )
    labels: list[ImageV2LabelEntryGQL] = strawberry.field(description="Docker labels.")
    status: ImageV2StatusGQL = strawberry.field(description="Image status (ALIVE or DELETED).")


@gql_pydantic_type(
    BackendAIGQLMeta(
        added_version="26.2.0",
        description="Runtime requirements information for an image. Contains resource limits and supported accelerators.",
    ),
    model=ImageRequirementsInfoDTO,
    name="ImageV2RequirementsInfo",
)
class ImageV2RequirementsInfoGQL:
    supported_accelerators: list[str] = strawberry.field(
        description="List of supported accelerator types (e.g., 'cuda', 'rocm')."
    )
    resource_limits: list[ImageV2ResourceLimitGQL] = strawberry.field(
        description="Resource slot limits (cpu, memory, accelerators, etc.)."
    )


@gql_pydantic_type(
    BackendAIGQLMeta(
        added_version="26.2.0",
        description="Permission information for an image. Contains the list of permissions the current user has on this image.",
    ),
    model=ImagePermissionInfoDTO,
    name="ImageV2PermissionInfo",
)
class ImageV2PermissionInfoGQL(PydanticOutputMixin[ImagePermissionInfoDTO]):
    permissions: list[ImageV2PermissionGQL] = strawberry.field(
        description="List of permissions the user has on this image."
    )


# =============================================================================
# Main Types
# =============================================================================


@gql_node_type(
    BackendAIGQLMeta(
        added_version="26.2.0",
        description="Represents a container image in Backend.AI. Images are container specifications that define the runtime environment for compute sessions. Each image has identity information, metadata, resource requirements, and permission settings. This is the V2 implementation using Strawberry GraphQL with Relay-style connections as part of BEP-1010 migration.",
    ),
    name="ImageV2",
)
class ImageV2GQL(PydanticNodeMixin[ImageNode]):
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
    def last_used(self) -> datetime | None:
        """Get the timestamp of the most recent session created with this image."""
        return self.metadata.last_used_at

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
        base_conditions = [ImageAliasConditions.by_image_ids([ImageID(self.id)])]
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
                node=ImageV2AliasGQL.from_pydantic(node),
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
        return cast(list[Self | None], results)


# Edge type using strawberry.relay.Edge
ImageV2EdgeGQL = Edge[ImageV2GQL]


@gql_connection_type(
    BackendAIGQLMeta(
        added_version="26.2.0",
        description="Relay-style connection for paginated image queries. Includes total count for pagination UI.",
    ),
    name="ImageV2Connection",
)
class ImageV2ConnectionGQL(Connection[ImageV2GQL]):
    count: int = strawberry.field(description="Total count of images matching the query.")

    def __init__(self, *args: Any, count: int, **kwargs: Any) -> None:
        super().__init__(*args, **kwargs)
        self.count = count


# =============================================================================
# Filter and OrderBy Types
# =============================================================================


@gql_pydantic_input(
    BackendAIGQLMeta(
        description="Scope for querying images within a specific container registry.",
        added_version="26.2.0",
    ),
    name="ContainerRegistryScope",
)
class ContainerRegistryScopeGQL(PydanticInputMixin[ContainerRegistryScopeInputDTO]):
    registry_id: uuid.UUID = strawberry.field(
        description="UUID of the container registry to scope the query to."
    )


@gql_pydantic_input(
    BackendAIGQLMeta(
        description="Scope for querying aliases within a specific image.",
        added_version="26.2.0",
    ),
    name="ImageV2Scope",
)
class ImageV2ScopeGQL(PydanticInputMixin[ImageScopeInputDTO]):
    image_id: uuid.UUID = strawberry.field(description="UUID of the image to scope the query to.")


@gql_pydantic_input(
    BackendAIGQLMeta(
        description="Nested filter for aliases belonging to an image. Filters images that have at least one alias matching all specified conditions.",
        added_version="26.3.0",
    ),
    name="ImageAliasNestedFilter",
)
class ImageAliasNestedFilterGQL(PydanticInputMixin[ImageAliasNestedFilterInputDTO]):
    """Nested filter for image aliases within an image."""

    alias: StringFilter | None = strawberry.field(
        default=None,
        description="Filter by alias string. Supports equals, contains, startsWith, and endsWith.",
    )


@gql_pydantic_input(
    BackendAIGQLMeta(
        description="Filter for image status with equality and membership operators.",
        added_version="26.3.0",
    ),
    name="ImageV2StatusFilter",
)
class ImageV2StatusFilterGQL(PydanticInputMixin[ImageStatusFilterInputDTO]):
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


@gql_pydantic_input(
    BackendAIGQLMeta(
        description="Filter options for images based on various criteria such as status, name, and architecture. Supports logical operations (AND, OR, NOT) for complex filtering scenarios.",
        added_version="26.2.0",
    ),
    name="ImageV2Filter",
)
class ImageV2FilterGQL(PydanticInputMixin[ImageFilterInputDTO], GQLFilter):
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
    AND: list[Self] | None = None
    OR: list[Self] | None = None
    NOT: list[Self] | None = None


@strawberry.enum(
    name="ImageV2OrderField",
    description=dedent_strip("""
    Added in 26.2.0.

    Fields available for ordering image queries.
    """),
)
class ImageV2OrderFieldGQL(StrEnum):
    NAME = "name"
    CREATED_AT = "created_at"
    LAST_USED = "last_used"


@gql_pydantic_input(
    BackendAIGQLMeta(
        description="Specifies the field and direction for ordering images in queries.",
        added_version="26.2.0",
    ),
)
class ImageV2OrderByGQL(PydanticInputMixin[ImageOrderByInputDTO], GQLOrderBy):
    field: ImageV2OrderFieldGQL
    direction: OrderDirection = OrderDirection.ASC


# =============================================================================
# Image Alias Types
# =============================================================================

# Edge type using strawberry.relay.Edge
ImageV2AliasEdgeGQL = Edge[ImageV2AliasGQL]


@gql_connection_type(
    BackendAIGQLMeta(
        added_version="26.2.0",
        description="Relay-style connection for paginated image alias queries. Includes total count for pagination UI.",
    ),
    name="ImageV2AliasConnection",
)
class ImageV2AliasConnectionGQL(Connection[ImageV2AliasGQL]):
    count: int = strawberry.field(description="Total count of aliases matching the query.")

    def __init__(self, *args: Any, count: int, **kwargs: Any) -> None:
        super().__init__(*args, **kwargs)
        self.count = count


@gql_pydantic_input(
    BackendAIGQLMeta(
        description="Filter options for image aliases. Supports filtering by alias string and image ID.",
        added_version="26.2.0",
    ),
    name="ImageV2AliasFilter",
)
class ImageV2AliasFilterGQL(PydanticInputMixin[ImageAliasFilterInputDTO], GQLFilter):
    alias: StringFilter | None = None
    image_id: UUIDFilter | None = strawberry.field(
        default=None,
        description="Added in 26.4.0. Filter by image ID.",
    )

    AND: list[Self] | None = None
    OR: list[Self] | None = None
    NOT: list[Self] | None = None


@strawberry.enum(
    name="ImageV2AliasOrderField",
    description=dedent_strip("""
    Added in 26.2.0.

    Fields available for ordering image alias queries.
    """),
)
class ImageV2AliasOrderFieldGQL(StrEnum):
    ALIAS = "alias"


@gql_pydantic_input(
    BackendAIGQLMeta(
        description="Specifies the field and direction for ordering image aliases in queries.",
        added_version="26.2.0",
    ),
)
class ImageV2AliasOrderByGQL(PydanticInputMixin[ImageAliasOrderByInputDTO], GQLOrderBy):
    field: ImageV2AliasOrderFieldGQL
    direction: OrderDirection = OrderDirection.ASC
