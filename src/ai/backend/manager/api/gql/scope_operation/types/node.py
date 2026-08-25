"""Scope operation GQL node."""

from __future__ import annotations

from strawberry.relay import NodeID

from ai.backend.common.dto.manager.v2.scope_operation.response import ScopeOperationNode
from ai.backend.common.meta.meta import NEXT_RELEASE_VERSION
from ai.backend.manager.api.gql.decorators import (
    BackendAIGQLMeta,
    gql_field,
    gql_node_type,
)
from ai.backend.manager.api.gql.pydantic_compat import PydanticNodeMixin

__all__ = ("ScopeOperationGQL",)


@gql_node_type(
    BackendAIGQLMeta(
        description=(
            "One operation the manager targets by scope rather than by entity id. The "
            "scope types it accepts are the action's own declaration, so this is what "
            "a permission over it may be configured at."
        ),
        added_version=NEXT_RELEASE_VERSION,
    ),
    name="ScopeOperation",
)
class ScopeOperationGQL(PydanticNodeMixin[ScopeOperationNode]):
    id: NodeID[str] = gql_field(description="The entity type and the action name, joined by `:`.")
    action_name: str = gql_field(description="The name the operation is recorded under.")
    entity_type: str = gql_field(description="The entity type the operation acts on.")
    operation: str = gql_field(description="The operation performed within the scopes.")
    scope_types: list[str] = gql_field(
        description=(
            "The scope types the operation may be targeted at; `global` where the "
            "caller names the scope type, empty where the operation names no scope."
        )
    )
