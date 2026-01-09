"""Revision fetcher functions."""

from __future__ import annotations

from functools import lru_cache
from typing import Optional
from uuid import UUID

from strawberry import Info
from strawberry.relay import PageInfo

from ai.backend.manager.api.gql.adapter import PaginationOptions, PaginationSpec
from ai.backend.manager.api.gql.base import encode_cursor
from ai.backend.manager.api.gql.deployment.types.revision import (
    ModelRevision,
    ModelRevisionConnection,
    ModelRevisionEdge,
    ModelRevisionFilter,
    ModelRevisionOrderBy,
)
from ai.backend.manager.api.gql.types import StrawberryGQLContext
from ai.backend.manager.repositories.base import QueryCondition
from ai.backend.manager.repositories.deployment.options import (
    RevisionConditions,
    RevisionOrders,
)
from ai.backend.manager.services.deployment.actions.model_revision.search_revisions import (
    SearchRevisionsAction,
)


@lru_cache(maxsize=1)
def get_revision_pagination_spec() -> PaginationSpec:
    return PaginationSpec(
        forward_order=RevisionOrders.created_at(ascending=False),
        backward_order=RevisionOrders.created_at(ascending=True),
        forward_condition_factory=RevisionConditions.by_cursor_forward,
        backward_condition_factory=RevisionConditions.by_cursor_backward,
    )


async def fetch_revisions(
    info: Info[StrawberryGQLContext],
    filter: Optional[ModelRevisionFilter] = None,
    order_by: Optional[list[ModelRevisionOrderBy]] = None,
    before: Optional[str] = None,
    after: Optional[str] = None,
    first: Optional[int] = None,
    last: Optional[int] = None,
    limit: Optional[int] = None,
    offset: Optional[int] = None,
    base_conditions: Optional[list[QueryCondition]] = None,
) -> ModelRevisionConnection:
    """Fetch revisions with optional filtering, ordering, and pagination.

    Args:
        info: GraphQL context info
        filter: Optional filter criteria
        order_by: Optional ordering specification
        before/after/first/last: Cursor-based pagination parameters
        limit/offset: Offset-based pagination parameters
        base_conditions: Additional conditions to prepend (e.g., deployment_id filter)
    """
    processor = info.context.processors.deployment

    # Build querier using gql_adapter
    querier = info.context.gql_adapter.build_querier(
        PaginationOptions(
            first=first,
            after=after,
            last=last,
            before=before,
            limit=limit,
            offset=offset,
        ),
        get_revision_pagination_spec(),
        filter=filter,
        order_by=order_by,
        base_conditions=base_conditions,
    )

    action_result = await processor.search_revisions.wait_for_complete(
        SearchRevisionsAction(querier=querier)
    )

    nodes = [ModelRevision.from_dataclass(data) for data in action_result.data]
    edges = [ModelRevisionEdge(node=node, cursor=encode_cursor(str(node.id))) for node in nodes]

    return ModelRevisionConnection(
        edges=edges,
        page_info=PageInfo(
            has_next_page=action_result.has_next_page,
            has_previous_page=action_result.has_previous_page,
            start_cursor=edges[0].cursor if edges else None,
            end_cursor=edges[-1].cursor if edges else None,
        ),
        count=action_result.total_count,
    )


async def fetch_revision(
    info: Info[StrawberryGQLContext],
    revision_id: UUID,
) -> Optional[ModelRevision]:
    """Fetch a specific revision by ID."""
    revision_data = await info.context.data_loaders.revision_loader.load(revision_id)
    if revision_data is None:
        return None
    return ModelRevision.from_dataclass(revision_data)
