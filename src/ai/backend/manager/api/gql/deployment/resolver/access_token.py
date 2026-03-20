"""Access token resolver functions."""

from __future__ import annotations

import strawberry
from strawberry import Info

from ai.backend.manager.api.gql.deployment.types.access_token import (
    AccessToken,
    CreateAccessTokenInput,
    CreateAccessTokenPayload,
)
from ai.backend.manager.api.gql.types import StrawberryGQLContext

# Mutation resolvers


@strawberry.mutation(description="Added in 25.16.0")  # type: ignore[misc]
async def create_access_token(
    input: CreateAccessTokenInput, info: Info[StrawberryGQLContext]
) -> CreateAccessTokenPayload:
    """Create a new access token for a deployment."""
    payload = await info.context.adapters.deployment.create_access_token(input.to_pydantic())
    return CreateAccessTokenPayload(access_token=AccessToken.from_pydantic(payload.access_token))
