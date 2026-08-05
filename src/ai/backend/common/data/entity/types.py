from abc import ABC, abstractmethod
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


class EntityData(ABC):
    """A ``data/`` type that can name the entity it represents.

    Inherited by the ``data/`` types of entities whose id has to be reported by a
    result rather than by an action — a create names a scope, so nothing upstream knows
    the id until the row exists, and the value that comes back is the only thing that
    does.

    An abstract method rather than an ``id`` field: several domains key on a name
    (``domains.name``, ``scaling_groups.name``, ``keypairs.access_key``) and map it to
    an ``EntityID`` themselves.
    """

    @abstractmethod
    def entity_id(self) -> EntityID:
        """Return the id of the entity this value describes."""
        raise NotImplementedError
