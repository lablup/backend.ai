"""GraphQL types for RBAC scope input and shared enums.

RBACElementTypeGQL is defined here (not in permission.py) to break the
circular import chain: entity_node → role → permission → entity_node.
Both permission.py and role.py can safely import from this module.
"""

from __future__ import annotations

from uuid import UUID

from ai.backend.common.dto.manager.v2.rbac.types import (
    EntityTypeScope,
    RBACElementTypeDTO,
    ScopeInputDTO,
    UUIDScope,
)
from ai.backend.common.dto.manager.v2.rbac.types import (
    RBACElementTypeFilter as RBACElementTypeFilterDTO,
)
from ai.backend.manager.api.gql.decorators import (
    BackendAIGQLMeta,
    PydanticInputMixin,
    gql_enum,
    gql_field,
    gql_pydantic_input,
)

# Re-export for stable import paths in audit_log scope
__all__ = (
    "EntityTypeScopeGQL",
    "RBACElementTypeFilterGQL",
    "RBACElementTypeGQL",
    "ScopeInputGQL",
    "UUIDScopeGQL",
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
        added_version="26.4.2",
    ),
    name="ScopeInput",
)
class ScopeInputGQL(PydanticInputMixin[ScopeInputDTO]):
    scope_type: RBACElementTypeGQL
    scope_id: str


@gql_pydantic_input(
    BackendAIGQLMeta(
        description="Entity reference parametrized by RBAC element type.",
        added_version="26.4.4",
    ),
    name="EntityTypeScope",
)
class EntityTypeScopeGQL(PydanticInputMixin[EntityTypeScope]):
    entity_type: RBACElementTypeGQL = gql_field(
        description="RBAC element type of the entity.",
    )
    entity_id: str = gql_field(
        description="ID of the entity.",
    )


@gql_pydantic_input(
    BackendAIGQLMeta(
        description="Single-UUID scope item wrapper.",
        added_version="26.4.4",
    ),
    name="UUIDScope",
)
class UUIDScopeGQL(PydanticInputMixin[UUIDScope]):
    value: UUID = gql_field(
        description="UUID value.",
    )


@gql_pydantic_input(
    BackendAIGQLMeta(
        description=(
            "Filter for RBAC element type fields (scope_type / entity_type). "
            "Supports equals / in / not_equals / not_in."
        ),
        added_version="26.4.4",
    ),
    name="RBACElementTypeFilter",
)
class RBACElementTypeFilterGQL(PydanticInputMixin[RBACElementTypeFilterDTO]):
    equals: RBACElementTypeGQL | None = gql_field(
        description="Matches rows with this exact element type.", default=None
    )
    in_: list[RBACElementTypeGQL] | None = gql_field(
        description="Matches rows whose element type is in this list.",
        name="in",
        default=None,
    )
    not_equals: RBACElementTypeGQL | None = gql_field(
        description="Excludes rows with this exact element type.", default=None
    )
    not_in: list[RBACElementTypeGQL] | None = gql_field(
        description="Excludes rows whose element type is in this list.", default=None
    )
