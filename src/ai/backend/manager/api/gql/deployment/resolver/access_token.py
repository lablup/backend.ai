"""Access token resolver functions."""

from __future__ import annotations

from uuid import UUID

from strawberry import Info

from ai.backend.common.meta.meta import NEXT_RELEASE_VERSION
from ai.backend.manager.api.gql.base import to_global_id
from ai.backend.manager.api.gql.decorators import (
    BackendAIGQLMeta,
    gql_mutation,
)
from ai.backend.manager.api.gql.deployment.types.access_token import (
    AccessToken,
    CreateAccessTokenInput,
    CreateAccessTokenPayload,
    DeleteAccessTokenInput,
    DeleteAccessTokenPayload,
    PartialBulkAccessTokensPayload,
    PartialBulkPurgeAccessTokensInput,
    PurgeAccessTokenPayload,
)
from ai.backend.manager.api.gql.types import StrawberryGQLContext

# Mutation resolvers


@gql_mutation(BackendAIGQLMeta(added_version="25.16.0", description="Create access token."))
async def create_access_token(
    input: CreateAccessTokenInput, info: Info[StrawberryGQLContext]
) -> CreateAccessTokenPayload | None:
    """Create a new access token for a deployment."""
    payload = await info.context.adapters.deployment.create_access_token(input.to_pydantic())
    return CreateAccessTokenPayload(access_token=AccessToken.from_pydantic(payload.access_token))


@gql_mutation(
    BackendAIGQLMeta(added_version="26.4.4", description="Delete access token."),
    deprecation_reason=f"Deprecated since {NEXT_RELEASE_VERSION}. Use `purgeAccessToken`.",
)
async def delete_access_token(
    input: DeleteAccessTokenInput, info: Info[StrawberryGQLContext]
) -> DeleteAccessTokenPayload | None:
    """Delete an access token."""
    payload = await info.context.adapters.deployment.purge_access_token(input.to_pydantic().id)
    return DeleteAccessTokenPayload(id=payload.id)


@gql_mutation(
    BackendAIGQLMeta(
        added_version=NEXT_RELEASE_VERSION, description="Permanently remove an access token."
    )
)
async def purge_access_token(id: UUID, info: Info[StrawberryGQLContext]) -> PurgeAccessTokenPayload:
    payload = await info.context.adapters.deployment.purge_access_token(id)
    return PurgeAccessTokenPayload.from_pydantic(
        payload, extra={"purged_id": to_global_id(AccessToken, payload.field_id)}
    )


@gql_mutation(
    BackendAIGQLMeta(
        added_version=NEXT_RELEASE_VERSION,
        description="Permanently remove several access tokens, answering for each one.",
    )
)
async def partial_bulk_purge_access_tokens(
    input: PartialBulkPurgeAccessTokensInput, info: Info[StrawberryGQLContext]
) -> PartialBulkAccessTokensPayload:
    payload = await info.context.adapters.deployment.partial_bulk_purge_access_tokens(
        input.to_pydantic()
    )
    return PartialBulkAccessTokensPayload.from_pydantic(payload)
