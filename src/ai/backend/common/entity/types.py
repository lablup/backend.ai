from dataclasses import dataclass
from typing import NewType

from ai.backend.common.identifier.entity import EntityID
from ai.backend.common.identifier.scope import ScopeID

EntityType = NewType("EntityType", str)
ScopeType = NewType("ScopeType", str)


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
