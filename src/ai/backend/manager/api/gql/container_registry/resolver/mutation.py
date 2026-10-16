"""Container Registry V2 GraphQL mutation resolvers."""

from __future__ import annotations

from uuid import UUID

from strawberry import Info

from ai.backend.common.data.entity.container_registry import ContainerRegistryID
from ai.backend.common.dto.manager.v2.container_registry.response import (
    DeleteContainerRegistryPayload,
)
from ai.backend.common.meta.meta import NEXT_RELEASE_VERSION
from ai.backend.manager.api.gql.base import parse_uuid
from ai.backend.manager.api.gql.container_registry.mutations import (
    CreateContainerRegistryInputGQL,
    CreateContainerRegistryPayloadGQL,
    DeleteContainerRegistryPayloadGQL,
    PartialBulkContainerRegistriesPayloadGQL,
    PartialBulkPurgeContainerRegistriesInputGQL,
    PurgeContainerRegistryPayloadGQL,
    UpdateContainerRegistryInputGQL,
    UpdateContainerRegistryPayloadGQL,
)
from ai.backend.manager.api.gql.decorators import (
    BackendAIGQLMeta,
    gql_mutation,
)
from ai.backend.manager.api.gql.types import StrawberryGQLContext
from ai.backend.manager.api.gql.utils import check_admin_only


@gql_mutation(
    BackendAIGQLMeta(
        added_version="26.4.2",
        description="Create a new container registry (admin only).",
    )
)
async def admin_create_container_registry_v2(
    info: Info[StrawberryGQLContext],
    input: CreateContainerRegistryInputGQL,
) -> CreateContainerRegistryPayloadGQL | None:
    check_admin_only()
    payload = await info.context.adapters.container_registry.admin_create(input.to_pydantic())
    return CreateContainerRegistryPayloadGQL.from_pydantic(payload)


@gql_mutation(
    BackendAIGQLMeta(
        added_version="26.4.2",
        description="Update a container registry (admin only).",
    )
)
async def admin_update_container_registry_v2(
    info: Info[StrawberryGQLContext],
    input: UpdateContainerRegistryInputGQL,
) -> UpdateContainerRegistryPayloadGQL | None:
    check_admin_only()
    payload = await info.context.adapters.container_registry.admin_update(input.to_pydantic())
    return UpdateContainerRegistryPayloadGQL.from_pydantic(payload)


@gql_mutation(
    BackendAIGQLMeta(
        added_version=NEXT_RELEASE_VERSION,
        description="Purge a container registry (admin only).",
    )
)
async def admin_purge_container_registry_v2(
    info: Info[StrawberryGQLContext],
    id: UUID,
) -> PurgeContainerRegistryPayloadGQL:
    check_admin_only()
    payload = await info.context.adapters.container_registry.admin_purge(ContainerRegistryID(id))
    return PurgeContainerRegistryPayloadGQL.from_pydantic(payload)


@gql_mutation(
    BackendAIGQLMeta(
        added_version=NEXT_RELEASE_VERSION,
        description="Purge several container registries (admin only), answering for each one.",
    )
)
async def admin_partial_bulk_purge_container_registries_v2(
    info: Info[StrawberryGQLContext],
    input: PartialBulkPurgeContainerRegistriesInputGQL,
) -> PartialBulkContainerRegistriesPayloadGQL:
    check_admin_only()
    payload = await info.context.adapters.container_registry.admin_partial_bulk_purge(
        input.to_pydantic()
    )
    return PartialBulkContainerRegistriesPayloadGQL.from_pydantic(payload)


@gql_mutation(
    BackendAIGQLMeta(
        added_version="26.4.2",
        description="Delete a container registry (admin only).",
    ),
    deprecation_reason=(
        f"Deprecated since {NEXT_RELEASE_VERSION}. Use `adminPurgeContainerRegistryV2`."
    ),
)
async def admin_delete_container_registry_v2(
    info: Info[StrawberryGQLContext],
    id: str,
) -> DeleteContainerRegistryPayloadGQL | None:
    check_admin_only()
    payload = await info.context.adapters.container_registry.admin_purge(
        ContainerRegistryID(parse_uuid(id))
    )
    return DeleteContainerRegistryPayloadGQL.from_pydantic(
        DeleteContainerRegistryPayload(id=payload.id)
    )
