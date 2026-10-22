"""GraphQL root resolver for the session lifecycle handler registry."""

from __future__ import annotations

from strawberry import Info

from ai.backend.common.meta.meta import NEXT_RELEASE_VERSION
from ai.backend.manager.api.gql.decorators import BackendAIGQLMeta, gql_root_field
from ai.backend.manager.api.gql.session_lifecycle_handler.types import (
    SessionLifecycleHandlerNodeGQL,
)
from ai.backend.manager.api.gql.types import StrawberryGQLContext
from ai.backend.manager.api.gql.utils import check_admin_only


@gql_root_field(
    BackendAIGQLMeta(
        added_version=NEXT_RELEASE_VERSION,
        description=(
            "List all registered session lifecycle handlers (superadmin only). "
            "The returned ``name`` values are valid keys for "
            "``DefaultSessionOptionsInfo.handlerOptions.byHandler``."
        ),
    )
)  # type: ignore[misc]
async def admin_session_lifecycle_handlers(
    info: Info[StrawberryGQLContext],
) -> list[SessionLifecycleHandlerNodeGQL] | None:
    """Return every registered session lifecycle handler."""
    check_admin_only()
    payload = (
        await info.context.adapters.session_lifecycle_handler.list_session_lifecycle_handlers()
    )
    return [SessionLifecycleHandlerNodeGQL.from_pydantic(node) for node in payload.items]
