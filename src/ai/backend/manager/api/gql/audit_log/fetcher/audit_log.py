from __future__ import annotations

from functools import lru_cache

import strawberry
from strawberry import Info

from ai.backend.manager.api.gql.adapter import PaginationOptions, PaginationSpec
from ai.backend.manager.api.gql.audit_log.types import (
    AuditLogFilterGQL,
    AuditLogOrderByGQL,
    AuditLogV2ConnectionGQL,
    AuditLogV2EdgeGQL,
    AuditLogV2GQL,
)
from ai.backend.manager.api.gql.base import encode_cursor
from ai.backend.manager.api.gql.types import StrawberryGQLContext
from ai.backend.manager.models.audit_log import AuditLogRow
from ai.backend.manager.repositories.audit_log.options import AuditLogOrders
from ai.backend.manager.services.audit_log.actions.search import SearchAuditLogsAction


@lru_cache(maxsize=1)
def _get_audit_log_pagination_spec() -> PaginationSpec:
    return PaginationSpec(
        forward_order=AuditLogOrders.created_at(ascending=False),
        backward_order=AuditLogOrders.created_at(ascending=True),
        forward_condition_factory=lambda _: lambda: AuditLogRow.created_at.isnot(None),
        backward_condition_factory=lambda _: lambda: AuditLogRow.created_at.isnot(None),
        tiebreaker_order=AuditLogRow.id.asc(),
    )


async def fetch_audit_logs(
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
    querier = info.context.gql_adapter.build_querier(
        PaginationOptions(
            first=first,
            after=after,
            last=last,
            before=before,
            limit=limit,
            offset=offset,
        ),
        pagination_spec=_get_audit_log_pagination_spec(),
        filter=filter,
        order_by=order_by,
    )

    action_result = await info.context.processors.audit_log.search.wait_for_complete(
        SearchAuditLogsAction(querier=querier)
    )

    nodes = [AuditLogV2GQL.from_data(data) for data in action_result.data]
    edges = [AuditLogV2EdgeGQL(node=node, cursor=encode_cursor(node.id)) for node in nodes]

    return AuditLogV2ConnectionGQL(
        edges=edges,
        page_info=strawberry.relay.PageInfo(
            has_next_page=action_result.has_next_page,
            has_previous_page=action_result.has_previous_page,
            start_cursor=edges[0].cursor if edges else None,
            end_cursor=edges[-1].cursor if edges else None,
        ),
        count=action_result.total_count,
    )
