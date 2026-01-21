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
from ai.backend.manager.services.deployment.actions.access_token.create_access_token import (
    CreateAccessTokenAction,
)

# Mutation resolvers


@strawberry.mutation(description="Added in 25.16.0")
async def create_access_token(
    input: CreateAccessTokenInput, info: Info[StrawberryGQLContext]
) -> CreateAccessTokenPayload:
    """Create a new access token for a deployment."""
    processor = info.context.processors.deployment
    result = await processor.create_access_token.wait_for_complete(
        action=CreateAccessTokenAction(input.to_creator())
    )
    return CreateAccessTokenPayload(access_token=AccessToken.from_dataclass(result.data))
