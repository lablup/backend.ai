"""GraphQL root resolver for the system session environ domain."""

from __future__ import annotations

from strawberry import Info

from ai.backend.common.meta.meta import NEXT_RELEASE_VERSION
from ai.backend.manager.api.gql.decorators import BackendAIGQLMeta, gql_root_field
from ai.backend.manager.api.gql.system_session_environ.types import (
    AdminResolveSystemSessionEnvironInputGQL,
    ResolveSystemSessionEnvironPayloadGQL,
)
from ai.backend.manager.api.gql.types import StrawberryGQLContext
from ai.backend.manager.api.gql.utils import check_admin_only


@gql_root_field(
    BackendAIGQLMeta(
        added_version=NEXT_RELEASE_VERSION,
        description=(
            "Read the system session environ rows a session in a domain and project receives, "
            "one per key (superadmin only)."
        ),
    )
)  # type: ignore[misc]
async def admin_resolve_system_session_environ(
    info: Info[StrawberryGQLContext],
    input: AdminResolveSystemSessionEnvironInputGQL,
) -> ResolveSystemSessionEnvironPayloadGQL | None:
    check_admin_only()
    payload = await info.context.adapters.system_session_environ.global_resolve(input.to_pydantic())
    return ResolveSystemSessionEnvironPayloadGQL.from_pydantic(payload)
