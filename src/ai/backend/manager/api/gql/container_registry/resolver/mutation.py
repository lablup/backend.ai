"""Container Registry V2 GraphQL mutation resolvers."""

from __future__ import annotations

from strawberry import Info

from ai.backend.common.dto.manager.v2.container_registry.request import (
    DeleteContainerRegistryInput,
)
from ai.backend.manager.api.gql.container_registry.mutations import (
    CreateContainerRegistryInputGQL,
    CreateContainerRegistryPayloadGQL,
    DeleteContainerRegistryPayloadGQL,
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
        added_version="26.4.2",
        description="Delete a container registry (admin only).",
    )
)
async def admin_delete_container_registry_v2(
    info: Info[StrawberryGQLContext],
    id: str,
) -> DeleteContainerRegistryPayloadGQL | None:
    check_admin_only()
    from uuid import UUID

    payload = await info.context.adapters.container_registry.admin_delete(
        DeleteContainerRegistryInput(id=UUID(id))
    )
    return DeleteContainerRegistryPayloadGQL.from_pydantic(payload)
