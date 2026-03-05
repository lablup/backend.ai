"""LoginSession GraphQL query resolvers."""

from __future__ import annotations

import strawberry
from strawberry import Info

from ai.backend.manager.api.gql.login_session.types.node import LoginSessionGQL
from ai.backend.manager.api.gql.types import StrawberryGQLContext


@strawberry.field(
    description=(
        "Added in 26.3.0. List all active login sessions for the currently authenticated user."
    )
)  # type: ignore[misc]
async def my_login_sessions(
    info: Info[StrawberryGQLContext],
) -> list[LoginSessionGQL]:
    """Return the list of active login sessions for the current user.

    Raises:
        NotImplementedError: This query is not yet implemented.
    """
    raise NotImplementedError("my_login_sessions is not yet implemented")
