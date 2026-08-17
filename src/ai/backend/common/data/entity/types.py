from __future__ import annotations

import uuid
from abc import ABC, abstractmethod
from dataclasses import dataclass
from typing import Any, NewType
from uuid import UUID

from pydantic import GetCoreSchemaHandler
from pydantic_core import CoreSchema, core_schema

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

    @classmethod
    def __get_pydantic_core_schema__(cls, source: Any, handler: GetCoreSchemaHandler) -> CoreSchema:
        """Validated as the string it is; pydantic builds no schema for a `str`
        subclass on its own."""
        return core_schema.no_info_after_validator_function(cls, core_schema.str_schema())


# Every entity doubles as a scope, so a scope type IS an entity type; the
# reverse direction stays an explicit declaration (`ScopeType(<entity type>)`).
ScopeType = NewType("ScopeType", EntityType)


class FieldType(str):
    """The type of a field row, which knows the type of entity that owns it.

    A class rather than a `NewType` for the same reason `EntityType` is one: the two
    must not be assignable to each other.
    """

    @classmethod
    @abstractmethod
    def owner_entity_type(cls) -> EntityType:
        raise NotImplementedError

    @classmethod
    def __get_pydantic_core_schema__(cls, source: Any, handler: GetCoreSchemaHandler) -> CoreSchema:
        """Validated as the string it is; pydantic builds no schema for a `str`
        subclass on its own."""
        return core_schema.no_info_after_validator_function(cls, core_schema.str_schema())


class NaturalKey(str):
    """A column value that forms part of a key drawn from the data itself.

    Names only itself: one column does not always identify a row, so which entity a
    key resolves is the lookup's declaration, not this value's.
    """

    @classmethod
    def key_name(cls) -> str:
        raise NotImplementedError

    @classmethod
    def __get_pydantic_core_schema__(cls, source: Any, handler: GetCoreSchemaHandler) -> CoreSchema:
        """Validated as the string it is; pydantic builds no schema for a `str`
        subclass on its own."""
        return core_schema.no_info_after_validator_function(cls, core_schema.str_schema())


@dataclass(frozen=True, slots=True)
class EntityRef:
    """An entity identified by its (open) type and id.

    Both are values read at run time — the graph layer reads them off a row — so the id
    is a bare one. Where the entity is known statically, pass an
    :class:`EntityIdentifier`, which needs no separate type beside it.
    """

    entity_type: EntityType
    entity_id: EntityID


@dataclass(frozen=True, slots=True)
class ScopeRef:
    """A scope identified by its (open) type and id.

    ``scope_type`` is a free-form string (NewType), not a fixed enum: the virtual
    scope layer accepts any owner type without extending a hard-coded scope enum.
    """

    scope_type: ScopeType
    scope_id: ScopeID

    def to_entity_ref(self) -> EntityRef:
        """An entity's scope identity is its entity identity: one pair serves both."""
        return EntityRef(entity_type=self.scope_type, entity_id=self.scope_id)


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

    @classmethod
    def __get_pydantic_core_schema__(cls, source: Any, handler: GetCoreSchemaHandler) -> CoreSchema:
        """Validated as the uuid it is; pydantic builds no schema for a `UUID`
        subclass on its own."""
        return core_schema.no_info_after_validator_function(cls, core_schema.uuid_schema())


class FieldIdentifier(UUID):
    """A field row's id, which knows its own type and the entity that owns it.

    No `entity_ref()`: a field row carries no membership of its own, so what it belongs
    to is only knowable through the entity that owns it.
    """

    def __init__(self, value: UUID) -> None:
        super().__init__(int=value.int)

    @classmethod
    @abstractmethod
    def field_type(cls) -> FieldType:
        raise NotImplementedError

    @classmethod
    def owner_entity_type(cls) -> EntityType:
        """Derived from the field type, which is where the ownership is declared."""
        return cls.field_type().owner_entity_type()

    @classmethod
    def __get_pydantic_core_schema__(cls, source: Any, handler: GetCoreSchemaHandler) -> CoreSchema:
        """Validated as the uuid it is; pydantic builds no schema for a `UUID`
        subclass on its own."""
        return core_schema.no_info_after_validator_function(cls, core_schema.uuid_schema())


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
    def entity_id(self) -> EntityIdentifier:
        """Return the id of the entity this value describes."""
        raise NotImplementedError


class FieldData(ABC):
    """A ``data/`` type describing a field row.

    Deliberately not an :class:`EntityData`: a field row carries no membership of its
    own, so what a result names is the entity owning it, not the row.
    """

    @abstractmethod
    def owner_entity_id(self) -> EntityIdentifier:
        """Return the id of the entity that owns the row this value describes."""
        raise NotImplementedError
