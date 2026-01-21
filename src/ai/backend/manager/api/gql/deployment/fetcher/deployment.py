"""Deployment fetcher functions."""

from __future__ import annotations

from functools import lru_cache
from typing import Optional
from uuid import UUID

from strawberry import Info
from strawberry.relay import PageInfo

from ai.backend.manager.api.gql.adapter import PaginationOptions, PaginationSpec
from ai.backend.manager.api.gql.base import encode_cursor
from ai.backend.manager.api.gql.deployment.types.deployment import (
    DeploymentFilter,
    DeploymentOrderBy,
    ModelDeployment,
    ModelDeploymentConnection,
    ModelDeploymentEdge,
)
from ai.backend.manager.api.gql.types import StrawberryGQLContext
from ai.backend.manager.repositories.deployment.options import (
    DeploymentConditions,
    DeploymentOrders,
)
from ai.backend.manager.services.deployment.actions.search_deployments import (
    SearchDeploymentsAction,
)


@lru_cache(maxsize=1)
def get_deployment_pagination_spec() -> PaginationSpec:
    return PaginationSpec(
        forward_order=DeploymentOrders.created_at(ascending=False),
        backward_order=DeploymentOrders.created_at(ascending=True),
        forward_condition_factory=DeploymentConditions.by_cursor_forward,
        backward_condition_factory=DeploymentConditions.by_cursor_backward,
    )


async def fetch_deployments(
    info: Info[StrawberryGQLContext],
    filter: Optional[DeploymentFilter] = None,
    order_by: Optional[list[DeploymentOrderBy]] = None,
    before: Optional[str] = None,
    after: Optional[str] = None,
    first: Optional[int] = None,
    last: Optional[int] = None,
    limit: Optional[int] = None,
    offset: Optional[int] = None,
) -> ModelDeploymentConnection:
    """Fetch deployments with optional filtering, ordering, and pagination."""
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
        get_deployment_pagination_spec(),
        filter=filter,
        order_by=order_by,
    )

    action_result = await processor.search_deployments.wait_for_complete(
        SearchDeploymentsAction(querier=querier)
    )

    nodes = [ModelDeployment.from_dataclass(data) for data in action_result.data]
    edges = [ModelDeploymentEdge(node=node, cursor=encode_cursor(str(node.id))) for node in nodes]

    return ModelDeploymentConnection(
        edges=edges,
        page_info=PageInfo(
            has_next_page=action_result.has_next_page,
            has_previous_page=action_result.has_previous_page,
            start_cursor=edges[0].cursor if edges else None,
            end_cursor=edges[-1].cursor if edges else None,
        ),
        count=action_result.total_count,
    )


async def fetch_deployment(
    info: Info[StrawberryGQLContext],
    deployment_id: UUID,
) -> Optional[ModelDeployment]:
    """Fetch a specific deployment by ID."""
    deployment_data = await info.context.data_loaders.deployment_loader.load(deployment_id)
    if deployment_data is None:
        return None
    return ModelDeployment.from_dataclass(deployment_data)
