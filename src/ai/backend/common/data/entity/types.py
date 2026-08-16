import uuid
from abc import ABC, abstractmethod
from dataclasses import dataclass
from typing import NewType
from uuid import UUID

# An entity's identifier. Polymorphic across entity kinds; the concrete kind is
# discriminated by the accompanying entity_type.
type EntityID = uuid.UUID
# A scope's identifier. Every scope doubles as an entity, so this is an alias of
# EntityID: the subset relation is visible in the type.
type ScopeID = EntityID


class EntityType(str):
    """The type of an entity.

    A class rather than a `NewType` so a `FieldType` cannot be passed where this is
    expected: two `NewType`s over `str` are mutually assignable.
    """


# Every entity doubles as a scope, so a scope type IS an entity type; the
# reverse direction stays an explicit declaration (`ScopeType(<entity type>)`).
ScopeType = NewType("ScopeType", EntityType)


class FieldType(str):
    """The type of a field row, which knows the entity that owns it."""

    @classmethod
    def owner_entity_type(cls) -> EntityType:
        raise NotImplementedError


class NaturalKey(str):
    """A column value that forms part of a key drawn from the data itself.

    Names only itself: one column does not always identify a row, so which entity a
    key resolves is the lookup's declaration, not this value's.
    """

    @classmethod
    def key_name(cls) -> str:
        raise NotImplementedError


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


class EntityIdentifier(UUID):
    """An entity's id, which knows the type it is an id of.

    Subclassing `UUID` keeps every value comparable and hashable against the plain
    ids already stored, so the change is additive at call sites.
    """

    def __init__(self, value: UUID) -> None:
        super().__init__(int=value.int)

    @classmethod
    @abstractmethod
    def entity_type(cls) -> EntityType:
        raise NotImplementedError

    def entity_ref(self) -> EntityRef:
        return EntityRef(entity_type=self.entity_type(), entity_id=self)


class FieldIdentifier(UUID):
    """A field row's id, which knows the type of the entity that owns it.

    No `entity_ref()`: a field row is absent from the RBAC graph, so there is
    nothing for it to name there.
    """

    def __init__(self, value: UUID) -> None:
        super().__init__(int=value.int)

    @classmethod
    @abstractmethod
    def owner_entity_type(cls) -> EntityType:
        raise NotImplementedError


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
