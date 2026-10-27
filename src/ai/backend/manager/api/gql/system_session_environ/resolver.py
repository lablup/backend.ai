"""GraphQL root resolver for the system session environ domain."""

from __future__ import annotations

from strawberry import Info

from ai.backend.common.meta.meta import NEXT_RELEASE_VERSION
from ai.backend.manager.api.gql.decorators import BackendAIGQLMeta, gql_root_field
from ai.backend.manager.api.gql.types import StrawberryGQLContext


@gql_root_field(
    BackendAIGQLMeta(
        added_version=NEXT_RELEASE_VERSION,
        description="List every value source name a system session environ row can carry.",
    )
)  # type: ignore[misc]
async def system_session_environ_value_sources(
    info: Info[StrawberryGQLContext],
) -> list[str] | None:
    payload = await info.context.adapters.system_session_environ.public_list_value_sources()
    return payload.items
