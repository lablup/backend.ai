"""GraphQL types for resource allocation."""

from __future__ import annotations

from uuid import UUID

from ai.backend.common.dto.manager.v2.resource_allocation.request import (
    AdminEffectiveResourceAllocationInput as AdminEffectiveResourceAllocationInputDTO,
)
from ai.backend.common.dto.manager.v2.resource_allocation.request import (
    CheckPresetAvailabilityInput as CheckPresetAvailabilityInputDTO,
)
from ai.backend.common.dto.manager.v2.resource_allocation.request import (
    EffectiveResourceAllocationInput as EffectiveResourceAllocationInputDTO,
)
from ai.backend.common.dto.manager.v2.resource_allocation.response import (
    CheckPresetAvailabilityPayload as CheckPresetAvailabilityPayloadDTO,
)
from ai.backend.common.dto.manager.v2.resource_allocation.response import (
    DomainResourceAllocationPayload as DomainResourceAllocationPayloadDTO,
)
from ai.backend.common.dto.manager.v2.resource_allocation.response import (
    EffectiveBreakdownNode as EffectiveBreakdownNodeDTO,
)
from ai.backend.common.dto.manager.v2.resource_allocation.response import (
    EffectiveResourceAllocationPayload as EffectiveResourceAllocationPayloadDTO,
)
from ai.backend.common.dto.manager.v2.resource_allocation.response import (
    KeypairResourceAllocationPayload as KeypairResourceAllocationPayloadDTO,
)
from ai.backend.common.dto.manager.v2.resource_allocation.response import (
    PresetAvailabilityNode as PresetAvailabilityNodeDTO,
)
from ai.backend.common.dto.manager.v2.resource_allocation.response import (
    ProjectResourceAllocationPayload as ProjectResourceAllocationPayloadDTO,
)
from ai.backend.common.dto.manager.v2.resource_allocation.response import (
    ResourceGroupResourceAllocationPayload as ResourceGroupResourceAllocationPayloadDTO,
)
from ai.backend.common.dto.manager.v2.resource_allocation.response import (
    ResourceGroupUsageNode as ResourceGroupUsageNodeDTO,
)
from ai.backend.common.dto.manager.v2.resource_allocation.response import (
    ScopeResourceUsageNode as ScopeResourceUsageNodeDTO,
)
from ai.backend.common.meta.meta import NEXT_RELEASE_VERSION
from ai.backend.manager.api.gql.common_types import (
    BinarySizeInfoGQL,
    ResourceLimitEntryGQL,
    ResourceSlotEntryGQL,
)
from ai.backend.manager.api.gql.decorators import (
    BackendAIGQLMeta,
    PydanticInputMixin,
    gql_field,
    gql_pydantic_input,
    gql_pydantic_type,
)
from ai.backend.manager.api.gql.pydantic_compat import PydanticOutputMixin

__all__ = (
    "AdminEffectiveResourceAllocationInputGQL",
    "CheckPresetAvailabilityInputGQL",
    "CheckPresetAvailabilityPayloadGQL",
    "DomainResourceAllocationPayloadGQL",
    "EffectiveBreakdownGQL",
    "EffectiveResourceAllocationInputGQL",
    "EffectiveResourceAllocationPayloadGQL",
    "KeypairResourceAllocationPayloadGQL",
    "PresetAvailabilityNodeGQL",
    "ProjectResourceAllocationPayloadGQL",
    "ResourceGroupResourceAllocationPayloadGQL",
    "ResourceGroupUsageGQL",
    "ScopeResourceUsageGQL",
)


# Output types


@gql_pydantic_type(
    BackendAIGQLMeta(
        added_version=NEXT_RELEASE_VERSION,
        description="Resource usage for a single scope (keypair, project, domain).",
    ),
    model=ScopeResourceUsageNodeDTO,
    name="ScopeResourceUsageV2",
)
class ScopeResourceUsageGQL(PydanticOutputMixin[ScopeResourceUsageNodeDTO]):
    limits: list[ResourceLimitEntryGQL] = gql_field(
        description="Policy-defined resource limits.",
    )
    used: list[ResourceSlotEntryGQL] = gql_field(
        description="Currently occupied resources.",
    )
    assignable: list[ResourceLimitEntryGQL] = gql_field(
        description="Assignable resources within policy limits (limits - used).",
    )


@gql_pydantic_type(
    BackendAIGQLMeta(
        added_version=NEXT_RELEASE_VERSION,
        description="Resource usage for a resource group (agent-level physical resources).",
    ),
    model=ResourceGroupUsageNodeDTO,
    name="ResourceGroupUsageV2",
)
class ResourceGroupUsageGQL(PydanticOutputMixin[ResourceGroupUsageNodeDTO]):
    capacity: list[ResourceSlotEntryGQL] = gql_field(
        description="Total agent capacity.",
    )
    used: list[ResourceSlotEntryGQL] = gql_field(
        description="Currently occupied by sessions.",
    )
    free: list[ResourceSlotEntryGQL] = gql_field(
        description="Free resources (capacity - used).",
    )
    max_per_node: list[ResourceSlotEntryGQL] = gql_field(
        description="Largest single-agent free resources.",
    )


@gql_pydantic_type(
    BackendAIGQLMeta(
        added_version=NEXT_RELEASE_VERSION,
        description="Breakdown of resource allocation by scope.",
    ),
    model=EffectiveBreakdownNodeDTO,
    name="EffectiveBreakdownV2",
)
class EffectiveBreakdownGQL(PydanticOutputMixin[EffectiveBreakdownNodeDTO]):
    keypair: ScopeResourceUsageGQL = gql_field(
        description="Keypair resource policy limits.",
    )
    project: ScopeResourceUsageGQL | None = gql_field(
        description="Project resource limits. Null when group_resource_visibility is disabled.",
    )
    domain: ScopeResourceUsageGQL = gql_field(
        description="Domain resource limits.",
    )
    resource_group: ResourceGroupUsageGQL | None = gql_field(
        description="Resource group physical resources. Null when hide_agents is enabled.",
    )


@gql_pydantic_type(
    BackendAIGQLMeta(
        added_version=NEXT_RELEASE_VERSION,
        description="Effective assignable resources considering all scope constraints.",
    ),
    model=EffectiveResourceAllocationPayloadDTO,
    name="EffectiveResourceAllocationV2",
)
class EffectiveResourceAllocationPayloadGQL(
    PydanticOutputMixin[EffectiveResourceAllocationPayloadDTO],
):
    assignable: list[ResourceLimitEntryGQL] = gql_field(
        description="Effective assignable resources (minimum across all scopes).",
    )
    breakdown: EffectiveBreakdownGQL = gql_field(
        description="Per-scope breakdown of resource limits and usage.",
    )


@gql_pydantic_type(
    BackendAIGQLMeta(
        added_version=NEXT_RELEASE_VERSION,
        description="A resource preset with its availability status.",
    ),
    model=PresetAvailabilityNodeDTO,
    name="PresetAvailabilityV2",
)
class PresetAvailabilityNodeGQL(PydanticOutputMixin[PresetAvailabilityNodeDTO]):
    id: str = gql_field(description="Resource preset UUID.")
    name: str = gql_field(description="Resource preset name.")
    resource_slots: list[ResourceSlotEntryGQL] = gql_field(
        description="Resource slot allocations.",
    )
    shared_memory: BinarySizeInfoGQL | None = gql_field(
        description="Shared memory size.",
    )
    resource_group_name: str | None = gql_field(
        description="Resource group name. Null means global preset.",
    )
    available: bool = gql_field(
        description="Whether this preset can be used for session creation.",
    )


@gql_pydantic_type(
    BackendAIGQLMeta(
        added_version=NEXT_RELEASE_VERSION,
        description="Payload containing preset availability check results.",
    ),
    model=CheckPresetAvailabilityPayloadDTO,
    name="CheckPresetAvailabilityPayloadV2",
)
class CheckPresetAvailabilityPayloadGQL(PydanticOutputMixin[CheckPresetAvailabilityPayloadDTO]):
    presets: list[PresetAvailabilityNodeGQL] = gql_field(
        description="Resource presets with availability status.",
    )


@gql_pydantic_type(
    BackendAIGQLMeta(
        added_version=NEXT_RELEASE_VERSION,
        description="Payload for keypair resource allocation query.",
    ),
    model=KeypairResourceAllocationPayloadDTO,
    name="KeypairResourceAllocationV2",
)
class KeypairResourceAllocationPayloadGQL(
    PydanticOutputMixin[KeypairResourceAllocationPayloadDTO],
):
    keypair: ScopeResourceUsageGQL = gql_field(
        description="Keypair resource usage.",
    )


@gql_pydantic_type(
    BackendAIGQLMeta(
        added_version=NEXT_RELEASE_VERSION,
        description="Payload for project resource allocation query.",
    ),
    model=ProjectResourceAllocationPayloadDTO,
    name="ProjectResourceAllocationV2",
)
class ProjectResourceAllocationPayloadGQL(
    PydanticOutputMixin[ProjectResourceAllocationPayloadDTO],
):
    project: ScopeResourceUsageGQL = gql_field(
        description="Project resource usage.",
    )


@gql_pydantic_type(
    BackendAIGQLMeta(
        added_version=NEXT_RELEASE_VERSION,
        description="Payload for domain resource allocation query.",
    ),
    model=DomainResourceAllocationPayloadDTO,
    name="DomainResourceAllocationV2",
)
class DomainResourceAllocationPayloadGQL(
    PydanticOutputMixin[DomainResourceAllocationPayloadDTO],
):
    domain: ScopeResourceUsageGQL = gql_field(
        description="Domain resource usage.",
    )


@gql_pydantic_type(
    BackendAIGQLMeta(
        added_version=NEXT_RELEASE_VERSION,
        description="Payload for resource group resource allocation query.",
    ),
    model=ResourceGroupResourceAllocationPayloadDTO,
    name="ResourceGroupResourceAllocationV2",
)
class ResourceGroupResourceAllocationPayloadGQL(
    PydanticOutputMixin[ResourceGroupResourceAllocationPayloadDTO],
):
    resource_group: ResourceGroupUsageGQL = gql_field(
        description="Resource group resource usage.",
    )


# Input types


@gql_pydantic_input(
    BackendAIGQLMeta(
        description="Input for querying effective assignable resources.",
        added_version=NEXT_RELEASE_VERSION,
    ),
    name="EffectiveResourceAllocationV2Input",
)
class EffectiveResourceAllocationInputGQL(
    PydanticInputMixin[EffectiveResourceAllocationInputDTO],
):
    project_id: UUID = gql_field(description="Project ID to check allocation for.")
    resource_group_name: str = gql_field(
        description="Resource group name to check allocation for.",
    )


@gql_pydantic_input(
    BackendAIGQLMeta(
        description="Input for admin querying effective assignable resources for a specific user.",
        added_version=NEXT_RELEASE_VERSION,
    ),
    name="AdminEffectiveResourceAllocationV2Input",
)
class AdminEffectiveResourceAllocationInputGQL(
    PydanticInputMixin[AdminEffectiveResourceAllocationInputDTO],
):
    user_id: UUID = gql_field(description="Target user ID.")
    project_id: UUID = gql_field(description="Project ID to check allocation for.")
    resource_group_name: str = gql_field(
        description="Resource group name to check allocation for.",
    )


@gql_pydantic_input(
    BackendAIGQLMeta(
        description="Input for checking which resource presets are available.",
        added_version=NEXT_RELEASE_VERSION,
    ),
    name="CheckPresetAvailabilityV2Input",
)
class CheckPresetAvailabilityInputGQL(
    PydanticInputMixin[CheckPresetAvailabilityInputDTO],
):
    project_id: UUID = gql_field(description="Project ID to check availability for.")
    resource_group_name: str = gql_field(
        description="Resource group name to check availability for.",
    )
