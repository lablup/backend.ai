"""GraphQL query resolvers for resource allocation."""

from __future__ import annotations

from uuid import UUID

from strawberry import Info

from ai.backend.common.meta.meta import NEXT_RELEASE_VERSION
from ai.backend.manager.api.gql.decorators import (
    BackendAIGQLMeta,
    gql_root_field,
)
from ai.backend.manager.api.gql.types import StrawberryGQLContext
from ai.backend.manager.api.gql.utils import check_admin_only

from .types import (
    AdminEffectiveResourceAllocationInputGQL,
    CheckPresetAvailabilityInputGQL,
    CheckPresetAvailabilityPayloadGQL,
    DomainResourceAllocationPayloadGQL,
    EffectiveResourceAllocationInputGQL,
    EffectiveResourceAllocationPayloadGQL,
    KeypairResourceAllocationPayloadGQL,
    ProjectResourceAllocationPayloadGQL,
    ResourceGroupResourceAllocationPayloadGQL,
)


@gql_root_field(
    BackendAIGQLMeta(
        added_version=NEXT_RELEASE_VERSION,
        description="Get my keypair resource allocation (current user).",
    )
)  # type: ignore[misc]
async def my_keypair_resource_allocation_v2(
    info: Info[StrawberryGQLContext],
) -> KeypairResourceAllocationPayloadGQL:
    payload = await info.context.adapters.resource_allocation.my_keypair_usage_for_current_user()
    return KeypairResourceAllocationPayloadGQL.from_pydantic(payload)


@gql_root_field(
    BackendAIGQLMeta(
        added_version=NEXT_RELEASE_VERSION,
        description="Get project resource allocation (project usage).",
    )
)  # type: ignore[misc]
async def project_resource_allocation_v2(
    info: Info[StrawberryGQLContext],
    project_id: UUID,
) -> ProjectResourceAllocationPayloadGQL:
    payload = await info.context.adapters.resource_allocation.project_usage(
        project_id=project_id,
    )
    return ProjectResourceAllocationPayloadGQL.from_pydantic(payload)


@gql_root_field(
    BackendAIGQLMeta(
        added_version=NEXT_RELEASE_VERSION,
        description="Get domain resource allocation (admin only).",
    )
)  # type: ignore[misc]
async def admin_domain_resource_allocation_v2(
    info: Info[StrawberryGQLContext],
    domain_name: str,
) -> DomainResourceAllocationPayloadGQL:
    check_admin_only()
    payload = await info.context.adapters.resource_allocation.admin_domain_usage(
        domain_name=domain_name,
    )
    return DomainResourceAllocationPayloadGQL.from_pydantic(payload)


@gql_root_field(
    BackendAIGQLMeta(
        added_version=NEXT_RELEASE_VERSION,
        description="Get resource group resource allocation.",
    )
)  # type: ignore[misc]
async def resource_group_resource_allocation_v2(
    info: Info[StrawberryGQLContext],
    resource_group_name: str,
) -> ResourceGroupResourceAllocationPayloadGQL:
    payload = await info.context.adapters.resource_allocation.resource_group_usage(
        rg_name=resource_group_name,
    )
    return ResourceGroupResourceAllocationPayloadGQL.from_pydantic(payload)


@gql_root_field(
    BackendAIGQLMeta(
        added_version=NEXT_RELEASE_VERSION,
        description="Get effective resource allocation for the current user.",
    )
)  # type: ignore[misc]
async def effective_resource_allocation_v2(
    info: Info[StrawberryGQLContext],
    input: EffectiveResourceAllocationInputGQL,
) -> EffectiveResourceAllocationPayloadGQL:
    payload = await info.context.adapters.resource_allocation.effective_allocation_for_current_user(
        input=input.to_pydantic(),
    )
    return EffectiveResourceAllocationPayloadGQL.from_pydantic(payload)


@gql_root_field(
    BackendAIGQLMeta(
        added_version=NEXT_RELEASE_VERSION,
        description="Get effective resource allocation for a specific user (admin only).",
    )
)  # type: ignore[misc]
async def admin_effective_resource_allocation_v2(
    info: Info[StrawberryGQLContext],
    input: AdminEffectiveResourceAllocationInputGQL,
) -> EffectiveResourceAllocationPayloadGQL:
    check_admin_only()
    payload = await info.context.adapters.resource_allocation.admin_effective_allocation_resolved(
        input=input.to_pydantic(),
    )
    return EffectiveResourceAllocationPayloadGQL.from_pydantic(payload)


@gql_root_field(
    BackendAIGQLMeta(
        added_version=NEXT_RELEASE_VERSION,
        description="Check which resource presets are available for session creation.",
    )
)  # type: ignore[misc]
async def check_preset_availability_v2(
    info: Info[StrawberryGQLContext],
    input: CheckPresetAvailabilityInputGQL,
) -> CheckPresetAvailabilityPayloadGQL:
    payload = (
        await info.context.adapters.resource_allocation.check_preset_availability_for_current_user(
            input=input.to_pydantic(),
        )
    )
    return CheckPresetAvailabilityPayloadGQL.from_pydantic(payload)
