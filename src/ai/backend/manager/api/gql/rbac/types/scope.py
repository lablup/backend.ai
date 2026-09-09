"""GraphQL types for RBAC scope input and shared enums."""

from __future__ import annotations

from ai.backend.common.dto.manager.v2.rbac.types import (
    EntityTypeFilter,
    EntityTypeScope,
    PermissionBitDTO,
    ScopeInputDTO,
)
from ai.backend.common.meta.meta import NEXT_RELEASE_VERSION
from ai.backend.manager.api.gql.decorators import (
    BackendAIGQLMeta,
    PydanticInputMixin,
    gql_enum,
    gql_field,
    gql_pydantic_input,
)

# Re-export for stable import paths in audit_log scope
__all__ = (
    "EntityTypeFilterGQL",
    "EntityTypeScopeGQL",
    "ScopeInputGQL",
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
    scope_type: str
    scope_id: str


@gql_pydantic_input(
    BackendAIGQLMeta(
        description="Entity reference parametrized by RBAC element type.",
        added_version="26.4.4",
    ),
    name="EntityTypeScope",
)
class EntityTypeScopeGQL(PydanticInputMixin[EntityTypeScope]):
    entity_type: str = gql_field(
        description="Type of the entity.",
    )
    entity_id: str = gql_field(
        description="ID of the entity.",
    )


@gql_pydantic_input(
    BackendAIGQLMeta(
        description="Filter for a field holding an entity type.",
        added_version=NEXT_RELEASE_VERSION,
    ),
    name="EntityTypeFilter",
)
class EntityTypeFilterGQL(PydanticInputMixin[EntityTypeFilter]):
    equals: str | None = gql_field(
        description="Matches rows with this exact entity type.", default=None
    )
    in_: list[str] | None = gql_field(
        description="Matches rows whose entity type is in this list.",
        name="in",
        default=None,
    )
    not_equals: str | None = gql_field(
        description="Excludes rows with this exact entity type.", default=None
    )
    not_in: list[str] | None = gql_field(
        description="Excludes rows whose entity type is in this list.", default=None
    )


PermissionBitGQL: type[PermissionBitDTO] = gql_enum(
    BackendAIGQLMeta(
        added_version=NEXT_RELEASE_VERSION,
        description="One bit of a permission mask; distinct from OperationType, which names an action.",
    ),
    PermissionBitDTO,
    name="PermissionBit",
)
