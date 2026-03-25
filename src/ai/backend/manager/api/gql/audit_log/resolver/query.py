from __future__ import annotations

import strawberry
from strawberry import Info

from ai.backend.common.dto.manager.v2.audit_log.request import AdminSearchAuditLogsInput
from ai.backend.manager.api.gql.audit_log.types import (
    AuditLogFilterGQL,
    AuditLogOrderByGQL,
    AuditLogV2ConnectionGQL,
    AuditLogV2EdgeGQL,
    AuditLogV2GQL,
)
from ai.backend.manager.api.gql.base import encode_cursor
from ai.backend.manager.api.gql.decorators import (
    BackendAIGQLMeta,
    gql_root_field,
)
from ai.backend.manager.api.gql.types import StrawberryGQLContext
from ai.backend.manager.api.gql.utils import check_admin_only


@gql_root_field(
    BackendAIGQLMeta(
        added_version="26.3.0",
        description="Query audit logs with pagination and filtering. (admin only)",
    )
)  # type: ignore[misc]
async def admin_audit_logs_v2(
    info: Info[StrawberryGQLContext],
    filter: AuditLogFilterGQL | None = None,
    order_by: list[AuditLogOrderByGQL] | None = None,
    before: str | None = None,
    after: str | None = None,
    first: int | None = None,
    last: int | None = None,
    limit: int | None = None,
    offset: int | None = None,
) -> AuditLogV2ConnectionGQL:
    check_admin_only()
    result = await info.context.adapters.audit_log.admin_search(
        AdminSearchAuditLogsInput(
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
    nodes = [AuditLogV2GQL.from_pydantic(item) for item in result.items]
    edges = [AuditLogV2EdgeGQL(node=node, cursor=encode_cursor(node.id)) for node in nodes]
    return AuditLogV2ConnectionGQL(
        edges=edges,
        page_info=strawberry.relay.PageInfo(
            has_next_page=result.has_next_page,
            has_previous_page=result.has_previous_page,
            start_cursor=edges[0].cursor if edges else None,
            end_cursor=edges[-1].cursor if edges else None,
        ),
        count=result.total_count,
    )
