"""Scope operation GQL query resolvers."""

from __future__ import annotations

from strawberry import Info

from ai.backend.common.meta.meta import NEXT_RELEASE_VERSION
from ai.backend.manager.api.gql.decorators import (
    BackendAIGQLMeta,
    gql_root_field,
)
from ai.backend.manager.api.gql.scope_operation.types import ScopeOperationGQL
from ai.backend.manager.api.gql.types import StrawberryGQLContext


@gql_root_field(
    BackendAIGQLMeta(
        description=(
            "Every operation the manager targets by scope, in entity type then name "
            "order, with the scope types each one accepts."
        ),
        added_version=NEXT_RELEASE_VERSION,
    )
)  # type: ignore[misc]
async def scope_operations(
    info: Info[StrawberryGQLContext],
) -> list[ScopeOperationGQL]:
    payload = info.context.adapters.scope_operation.list_scope_operations()
    return [
        ScopeOperationGQL.from_pydantic(
            item, extra={"id": f"{item.entity_type}:{item.action_name}"}
        )
        for item in payload.items
    ]
