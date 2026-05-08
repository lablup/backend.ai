"""GraphQL root resolver for the scheduling-handler registry."""

from __future__ import annotations

from strawberry import Info

from ai.backend.common.meta.meta import NEXT_RELEASE_VERSION
from ai.backend.manager.api.gql.decorators import BackendAIGQLMeta, gql_root_field
from ai.backend.manager.api.gql.scheduling_handler.types import SchedulingHandlerNodeGQL
from ai.backend.manager.api.gql.types import StrawberryGQLContext
from ai.backend.manager.api.gql.utils import check_admin_only


@gql_root_field(
    BackendAIGQLMeta(
        added_version=NEXT_RELEASE_VERSION,
        description=(
            "List all registered deployment scheduling handlers (superadmin only). "
            "The returned ``name`` values are valid keys for "
            "``DeploymentOptions.handler_options.by_handler``."
        ),
    )
)  # type: ignore[misc]
async def scheduling_handlers(
    info: Info[StrawberryGQLContext],
) -> list[SchedulingHandlerNodeGQL] | None:
    """Return every registered deployment scheduling handler."""
    check_admin_only()
    payload = await info.context.adapters.scheduling_handler.list_scheduling_handlers()
    return [SchedulingHandlerNodeGQL.from_pydantic(node) for node in payload.items]
