"""GraphQL types for resource preset."""

from __future__ import annotations

from enum import StrEnum
from typing import Any, Self
from uuid import UUID

from strawberry.relay import Connection, Edge, NodeID

from ai.backend.common.dto.manager.v2.resource_preset.request import (
    CreateResourcePresetInput as CreateResourcePresetInputDTO,
)
from ai.backend.common.dto.manager.v2.resource_preset.request import (
    ResourcePresetFilter as ResourcePresetFilterDTO,
)
from ai.backend.common.dto.manager.v2.resource_preset.request import (
    ResourcePresetOrder as ResourcePresetOrderDTO,
)
from ai.backend.common.dto.manager.v2.resource_preset.request import (
    UpdateResourcePresetInput as UpdateResourcePresetInputDTO,
)
from ai.backend.common.dto.manager.v2.resource_preset.response import (
    CreateResourcePresetPayload as CreateResourcePresetPayloadDTO,
)
from ai.backend.common.dto.manager.v2.resource_preset.response import (
    DeleteResourcePresetPayload as DeleteResourcePresetPayloadDTO,
)
from ai.backend.common.dto.manager.v2.resource_preset.response import (
    ResourcePresetNode,
)
from ai.backend.common.dto.manager.v2.resource_preset.response import (
    UpdateResourcePresetPayload as UpdateResourcePresetPayloadDTO,
)
from ai.backend.common.meta.meta import NEXT_RELEASE_VERSION
from ai.backend.manager.api.gql.base import OrderDirection, StringFilter
from ai.backend.manager.api.gql.common_types import (
    BinarySizeInfoGQL,
    BinarySizeInputGQL,
    ResourceSlotEntryGQL,
    ResourceSlotEntryInputGQL,
)
from ai.backend.manager.api.gql.decorators import (
    BackendAIGQLMeta,
    PydanticInputMixin,
    gql_connection_type,
    gql_enum,
    gql_field,
    gql_node_type,
    gql_pydantic_input,
    gql_pydantic_type,
)
from ai.backend.manager.api.gql.pydantic_compat import PydanticNodeMixin, PydanticOutputMixin

__all__ = (
    "CreateResourcePresetInputGQL",
    "CreateResourcePresetPayloadGQL",
    "DeleteResourcePresetPayloadGQL",
    "ResourcePresetConnection",
    "ResourcePresetFilterGQL",
    "ResourcePresetGQL",
    "ResourcePresetOrderByGQL",
    "ResourcePresetOrderFieldGQL",
    "UpdateResourcePresetInputGQL",
    "UpdateResourcePresetPayloadGQL",
)


@gql_enum(
    BackendAIGQLMeta(
        added_version=NEXT_RELEASE_VERSION,
        description="Fields available for ordering resource presets.",
    ),
    name="ResourcePresetOrderField",
)
class ResourcePresetOrderFieldGQL(StrEnum):
    """Resource preset order field enumeration for GraphQL."""

    NAME = "name"


@gql_node_type(
    BackendAIGQLMeta(
        added_version=NEXT_RELEASE_VERSION,
        description="Resource preset with resource slot allocations.",
    ),
    name="ResourcePresetV2",
)
class ResourcePresetGQL(PydanticNodeMixin[ResourcePresetNode]):
    id: NodeID[str] = gql_field(
        description="Relay-style global node identifier for the resource preset."
    )
    name: str = gql_field(description="Resource preset name.")
    resource_slots: list[ResourceSlotEntryGQL] = gql_field(
        description="Resource slot allocations for this preset."
    )
    shared_memory: BinarySizeInfoGQL | None = gql_field(
        description="Shared memory size with both bytes and human-readable format."
    )
    resource_group_name: str | None = gql_field(
        description="Resource group name. Null means global preset."
    )


# Filter and OrderBy types


@gql_pydantic_input(
    BackendAIGQLMeta(
        description="Filter for resource presets.", added_version=NEXT_RELEASE_VERSION
    ),
    name="ResourcePresetFilter",
)
class ResourcePresetFilterGQL(PydanticInputMixin[ResourcePresetFilterDTO]):
    name: StringFilter | None = None
    resource_group_name: StringFilter | None = None

    AND: list[Self] | None = None
    OR: list[Self] | None = None
    NOT: list[Self] | None = None


@gql_pydantic_input(
    BackendAIGQLMeta(
        description="Order by specification for resource presets.",
        added_version=NEXT_RELEASE_VERSION,
    ),
    name="ResourcePresetOrderBy",
)
class ResourcePresetOrderByGQL(PydanticInputMixin[ResourcePresetOrderDTO]):
    field: ResourcePresetOrderFieldGQL
    direction: OrderDirection = OrderDirection.ASC


# Mutation Input/Payload types


@gql_pydantic_input(
    BackendAIGQLMeta(
        description="Input for creating a new resource preset.",
        added_version=NEXT_RELEASE_VERSION,
    ),
    name="CreateResourcePresetV2Input",
)
class CreateResourcePresetInputGQL(PydanticInputMixin[CreateResourcePresetInputDTO]):
    name: str = gql_field(description="Resource preset name.")
    resource_slots: list[ResourceSlotEntryInputGQL] = gql_field(
        description="Resource slot allocations."
    )
    shared_memory: BinarySizeInputGQL | None = gql_field(
        default=None,
        description="Shared memory size (e.g., expr: '512m' or '536870912').",
    )
    resource_group_name: str | None = gql_field(
        default=None,
        description="Resource group name. If null, the preset is global.",
    )


@gql_pydantic_type(
    BackendAIGQLMeta(
        added_version=NEXT_RELEASE_VERSION,
        description="Payload for resource preset creation.",
    ),
    model=CreateResourcePresetPayloadDTO,
)
class CreateResourcePresetPayloadGQL(PydanticOutputMixin[CreateResourcePresetPayloadDTO]):
    resource_preset: ResourcePresetGQL = gql_field(description="The created resource preset.")


@gql_pydantic_input(
    BackendAIGQLMeta(
        description="Input for updating a resource preset. All fields optional for partial update.",
        added_version=NEXT_RELEASE_VERSION,
    ),
    name="UpdateResourcePresetV2Input",
)
class UpdateResourcePresetInputGQL(PydanticInputMixin[UpdateResourcePresetInputDTO]):
    id: UUID = gql_field(description="UUID of the resource preset to update.")
    name: str | None = gql_field(default=None, description="Updated name.")
    resource_slots: list[ResourceSlotEntryInputGQL] | None = gql_field(
        default=None, description="Updated resource slot allocations."
    )
    shared_memory: BinarySizeInputGQL | None = gql_field(
        default=None,
        description="Updated shared memory. Use null to clear.",
    )
    resource_group_name: str | None = gql_field(
        default=None,
        description="Updated resource group name. Use null to make global.",
    )


@gql_pydantic_type(
    BackendAIGQLMeta(
        added_version=NEXT_RELEASE_VERSION,
        description="Payload for resource preset update.",
    ),
    model=UpdateResourcePresetPayloadDTO,
)
class UpdateResourcePresetPayloadGQL(PydanticOutputMixin[UpdateResourcePresetPayloadDTO]):
    resource_preset: ResourcePresetGQL = gql_field(description="The updated resource preset.")


@gql_pydantic_type(
    BackendAIGQLMeta(
        added_version=NEXT_RELEASE_VERSION,
        description="Payload for resource preset deletion.",
    ),
    model=DeleteResourcePresetPayloadDTO,
)
class DeleteResourcePresetPayloadGQL(PydanticOutputMixin[DeleteResourcePresetPayloadDTO]):
    id: str = gql_field(description="UUID of the deleted resource preset.")


# Connection type


ResourcePresetEdge = Edge[ResourcePresetGQL]


@gql_connection_type(
    BackendAIGQLMeta(
        added_version=NEXT_RELEASE_VERSION,
        description="Resource preset connection.",
    )
)
class ResourcePresetConnection(Connection[ResourcePresetGQL]):
    count: int

    def __init__(self, *args: Any, count: int, **kwargs: Any) -> None:
        super().__init__(*args, **kwargs)
        self.count = count
