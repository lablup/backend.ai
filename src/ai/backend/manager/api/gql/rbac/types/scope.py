"""GraphQL types for RBAC scope input and shared enums.

RBACElementTypeGQL is defined here (not in permission.py) to break the
circular import chain: entity_node → role → permission → entity_node.
Both permission.py and role.py can safely import from this module.
"""

from __future__ import annotations

from ai.backend.common.dto.manager.v2.rbac.types import (
    RBACElementTypeDTO,
    ScopeInputDTO,
)
from ai.backend.common.meta.meta import NEXT_RELEASE_VERSION
from ai.backend.manager.api.gql.decorators import (
    BackendAIGQLMeta,
    PydanticInputMixin,
    gql_enum,
    gql_pydantic_input,
)

# ==================== Enums ====================

RBACElementTypeGQL: type[RBACElementTypeDTO] = gql_enum(
    BackendAIGQLMeta(
        added_version="26.3.0",
        description="Unified RBAC element type for scope-entity relationships",
    ),
    RBACElementTypeDTO,
    name="RBACElementType",
)

# ==================== Input Types ====================


@gql_pydantic_input(
    BackendAIGQLMeta(
        description="Scope reference for associating an entity with a scope.",
        added_version=NEXT_RELEASE_VERSION,
    ),
    name="ScopeInput",
)
class ScopeInputGQL(PydanticInputMixin[ScopeInputDTO]):
    scope_type: RBACElementTypeGQL
    scope_id: str
