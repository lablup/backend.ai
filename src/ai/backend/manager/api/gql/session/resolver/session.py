from __future__ import annotations

from uuid import UUID

import strawberry
from strawberry import ID, Info

from ai.backend.common.contexts.user import current_user
from ai.backend.common.dto.manager.v2.session.request import (
    AdminSearchSessionsInput,
    TerminateSessionsInProjectInput,
)
from ai.backend.common.meta.meta import NEXT_RELEASE_VERSION
from ai.backend.manager.api.gql.base import encode_cursor
from ai.backend.manager.api.gql.decorators import (
    BackendAIGQLMeta,
    gql_mutation,
    gql_root_field,
)
from ai.backend.manager.api.gql.session.types import (
    EnqueueSessionInputGQL,
    EnqueueSessionPayloadGQL,
    ProjectSessionScopeGQL,
    SessionV2ConnectionGQL,
    SessionV2EdgeGQL,
    SessionV2FilterGQL,
    SessionV2GQL,
    SessionV2OrderByGQL,
    TerminateSessionsPayloadGQL,
)
from ai.backend.manager.api.gql.types import StrawberryGQLContext
from ai.backend.manager.api.gql.utils import check_admin_only
from ai.backend.manager.errors.user import UserNotFound


@gql_root_field(
    BackendAIGQLMeta(
        added_version="26.3.0",
        description="Query sessions with pagination and filtering. (admin only)",
    )
)  # type: ignore[misc]
async def admin_sessions_v2(
    info: Info[StrawberryGQLContext],
    filter: SessionV2FilterGQL | None = None,
    order_by: list[SessionV2OrderByGQL] | None = None,
    before: str | None = None,
    after: str | None = None,
    first: int | None = None,
    last: int | None = None,
    limit: int | None = None,
    offset: int | None = None,
) -> SessionV2ConnectionGQL:
    check_admin_only()
    payload = await info.context.adapters.session.admin_search(
        AdminSearchSessionsInput(
            filter=filter.to_pydantic() if filter else None,
            order=[o.to_pydantic() for o in order_by] if order_by else None,
            first=first,
            after=after,
            last=last,
            before=before,
            limit=limit,
            offset=offset,
        )
    )
    nodes = [SessionV2GQL.from_pydantic(node) for node in payload.items]
    edges = [SessionV2EdgeGQL(node=node, cursor=encode_cursor(node.id)) for node in nodes]
    return SessionV2ConnectionGQL(
        edges=edges,
        page_info=strawberry.relay.PageInfo(
            has_next_page=payload.has_next_page,
            has_previous_page=payload.has_previous_page,
            start_cursor=edges[0].cursor if edges else None,
            end_cursor=edges[-1].cursor if edges else None,
        ),
        count=payload.total_count,
    )


@gql_mutation(
    BackendAIGQLMeta(
        added_version=NEXT_RELEASE_VERSION,
        description="Enqueue a new compute session.",
    ),
)  # type: ignore[misc]
async def enqueue_session(
    input: EnqueueSessionInputGQL,
    info: Info[StrawberryGQLContext],
) -> EnqueueSessionPayloadGQL:
    """Enqueue a new compute session (interactive or batch)."""
    user_data = current_user()
    if user_data is None:
        raise UserNotFound("User not found in context")
    pydantic_input = input.to_pydantic()
    payload = await info.context.adapters.session.enqueue(
        pydantic_input,
        user_id=user_data.user_id,
        user_role=str(user_data.role),
        access_key="",
        domain_name=user_data.domain_name,
        group_id=pydantic_input.project_id,
    )
    return EnqueueSessionPayloadGQL(
        session=SessionV2GQL.from_pydantic(payload.session),
    )


@gql_mutation(
    BackendAIGQLMeta(
        added_version=NEXT_RELEASE_VERSION,
        description="Terminate sessions within a project scope.",
    ),
)  # type: ignore[misc]
async def terminate_project_sessions_v2(
    info: Info[StrawberryGQLContext],
    scope: ProjectSessionScopeGQL,
    session_ids: list[ID],
    forced: bool = False,
) -> TerminateSessionsPayloadGQL:
    """Terminate one or more sessions scoped to a project."""
    payload = await info.context.adapters.session.terminate_in_project(
        TerminateSessionsInProjectInput(
            project_id=scope.project_id,
            session_ids=[UUID(str(sid)) for sid in session_ids],
            forced=forced,
        )
    )
    return TerminateSessionsPayloadGQL(
        cancelled=[ID(str(sid)) for sid in payload.cancelled],
        terminating=[ID(str(sid)) for sid in payload.terminating],
        force_terminated=[ID(str(sid)) for sid in payload.force_terminated],
        skipped=[ID(str(sid)) for sid in payload.skipped],
    )
