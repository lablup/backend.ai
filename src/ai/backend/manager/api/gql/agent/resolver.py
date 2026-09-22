from __future__ import annotations

from typing import Annotated, cast

import strawberry
from strawberry import Info
from strawberry.scalars import JSON

from ai.backend.common.dto.manager.v2.agent.request import AdminSearchAgentsInput
from ai.backend.common.meta.meta import NEXT_RELEASE_VERSION
from ai.backend.manager.api.gql.agent.types import (
    AgentFilterGQL,
    AgentOrderByGQL,
    AgentResourceGQL,
    AgentStatsGQL,
    AgentUsageGQL,
    AgentV2Connection,
    AgentV2Edge,
    AgentV2GQL,
    UpdateAgentResourceGroupInputGQL,
    UpdateAgentResourceGroupPayloadGQL,
)
from ai.backend.manager.api.gql.base import encode_cursor
from ai.backend.manager.api.gql.decorators import (
    BackendAIGQLMeta,
    gql_mutation,
    gql_root_field,
)
from ai.backend.manager.api.gql.types import StrawberryGQLContext
from ai.backend.manager.api.gql.utils import check_admin_only


@gql_root_field(
    BackendAIGQLMeta(added_version="25.15.0", description="Get aggregate agent resource statistics")
)  # type: ignore[misc]
async def agent_stats(info: Info[StrawberryGQLContext]) -> AgentStatsGQL | None:
    check_admin_only()
    total = await info.context.adapters.agent.get_total_resources()
    resource = AgentResourceGQL(
        free=cast(JSON, total.total_free_slots.to_json()),
        used=cast(JSON, total.total_used_slots.to_json()),
        capacity=cast(JSON, total.total_capacity_slots.to_json()),
    )
    return AgentStatsGQL(total_resource=resource)


@gql_root_field(
    BackendAIGQLMeta(
        added_version="26.1.0", description="List agents with filtering and pagination"
    )
)  # type: ignore[misc]
async def agents_v2(
    info: Info[StrawberryGQLContext],
    usage: Annotated[
        AgentUsageGQL | None,
        strawberry.argument(
            description=(
                f"Added in {NEXT_RELEASE_VERSION}. Uses narrowing the result. Each listed "
                "entity must be readable by the caller; agents the caller cannot read are "
                "left out."
            )
        ),
    ] = None,
    filter: AgentFilterGQL | None = None,
    order_by: list[AgentOrderByGQL] | None = None,
    before: str | None = None,
    after: str | None = None,
    first: int | None = None,
    last: int | None = None,
    limit: int | None = None,
    offset: int | None = None,
) -> AgentV2Connection | None:
    check_admin_only()
    result = await info.context.adapters.agent.admin_search(
        AdminSearchAgentsInput(
            usage=usage.to_pydantic() if usage else None,
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
    nodes = [AgentV2GQL.from_pydantic(item) for item in result.items]
    edges = [AgentV2Edge(node=node, cursor=encode_cursor(node.entity_id)) for node in nodes]
    return AgentV2Connection(
        edges=edges,
        page_info=strawberry.relay.PageInfo(
            has_next_page=result.has_next_page,
            has_previous_page=result.has_previous_page,
            start_cursor=edges[0].cursor if edges else None,
            end_cursor=edges[-1].cursor if edges else None,
        ),
        count=result.total_count,
    )


@gql_mutation(
    BackendAIGQLMeta(
        added_version="26.8.0",
        description=(
            "Change the resource group of an agent (superadmin only). Sessions still running"
            " on the agent under the old resource group are cleaned up per the given policy;"
            " without force, the change is rejected with a conflict error when such sessions"
            " exist."
        ),
    )
)
async def admin_update_agent_resource_group(
    info: Info[StrawberryGQLContext],
    input: UpdateAgentResourceGroupInputGQL,
) -> UpdateAgentResourceGroupPayloadGQL | None:
    """Change an agent's resource group."""
    check_admin_only()
    payload = await info.context.adapters.agent.update_resource_group(input.to_pydantic())
    return UpdateAgentResourceGroupPayloadGQL.from_pydantic(payload)
