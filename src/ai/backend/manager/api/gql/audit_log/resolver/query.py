from __future__ import annotations

import strawberry
from strawberry import Info

from ai.backend.manager.api.gql.audit_log.fetcher import fetch_audit_logs
from ai.backend.manager.api.gql.audit_log.types import (
    AuditLogFilterGQL,
    AuditLogOrderByGQL,
    AuditLogV2ConnectionGQL,
)
from ai.backend.manager.api.gql.types import StrawberryGQLContext
from ai.backend.manager.api.gql.utils import check_admin_only


@strawberry.field(description="Query audit logs with pagination and filtering. (admin only)")  # type: ignore[misc]
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
    return await fetch_audit_logs(
        info,
        filter=filter,
        order_by=order_by,
        before=before,
        after=after,
        first=first,
        last=last,
        limit=limit,
        offset=offset,
    )
