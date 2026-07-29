from dataclasses import dataclass
from typing import NewType

from ai.backend.common.identifier.entity import EntityID
from ai.backend.common.identifier.scope import ScopeID

EntityType = NewType("EntityType", str)
ScopeType = NewType("ScopeType", str)

# Canonical scope/entity type values. Only types that already exist in
# RBACElementType (i.e. are managed by RBAC) share its value; new types are
# defined as raw strings without consulting RBACElementType.
DOMAIN_SCOPE_TYPE = ScopeType("domain")
PROJECT_SCOPE_TYPE = ScopeType("project")
USER_SCOPE_TYPE = ScopeType("user")
USER_ENTITY_TYPE = EntityType("user")


@dataclass(frozen=True, slots=True)
class ScopeRef:
    """A scope identified by its (open) type and id.

    ``scope_type`` is a free-form string (NewType), not a fixed enum: the virtual
    scope layer accepts any owner type without extending a hard-coded scope enum.
    """

    scope_type: ScopeType
    scope_id: ScopeID


@dataclass(frozen=True, slots=True)
class EntityRef:
    """An entity identified by its (open) type and id."""

    entity_type: EntityType
    entity_id: EntityID
