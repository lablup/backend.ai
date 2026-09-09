from __future__ import annotations

import uuid
from abc import ABC, abstractmethod
from collections.abc import Iterator
from typing import Any, NewType, Self, override
from uuid import UUID

from pydantic import GetCoreSchemaHandler
from pydantic_core import CoreSchema, core_schema

# An entity's identifier. Polymorphic across entity kinds; the concrete kind is
# discriminated by the accompanying entity_type.
type EntityID = uuid.UUID


class EntityType(str):
    """The type of an entity.

    A class rather than a `NewType` so a `NaturalKey` cannot be passed where this is
    expected: two `NewType`s over `str` are mutually assignable.

    One subclass per kind, built with no argument: ``AgentEntityType()``. Do not
    declare a module-level instance of one.

    ``EntityType(value)`` rebuilds the bare base from a string and answers no `name()`
    or `description()`. Reserved for a boundary that reads one -- a row column, a
    legacy action, an RBAC element -- and written nowhere else.
    """

    def __new__(cls, value: str | None = None) -> Self:
        """A kind is built with no argument. Passing a value rebuilds the bare base from
        a string, which the rules below reserve for a boundary reading one."""
        return super().__new__(cls, cls.name() if value is None else value)

    @override
    def __reduce__(self) -> tuple[type[Any], tuple[Any, ...]]:
        if type(self) is EntityType:
            return (EntityType, (str(self),))
        return (type(self), ())

    @classmethod
    def name(cls) -> str:
        raise NotImplementedError

    @classmethod
    def description(cls) -> str:
        raise NotImplementedError

    @classmethod
    def from_name(cls, name: str) -> EntityType:
        """The kind answering to ``name``, or the bare base when none does.

        A kind is found only once its module is imported, so a caller matching on kinds
        imports the ones it handles. What is left over is a type this build does not
        declare, and the bare base is what it is.
        """
        for kind in cls._kinds():
            if kind.name() == name:
                return kind()
        return EntityType(name)

    @classmethod
    def _kinds(cls) -> Iterator[type[EntityType]]:
        for kind in cls.__subclasses__():
            yield kind
            yield from kind._kinds()

    @classmethod
    def __get_pydantic_core_schema__(cls, source: Any, handler: GetCoreSchemaHandler) -> CoreSchema:
        """Validated as the string it is; pydantic builds no schema for a `str`
        subclass on its own. A kind accepts its own name alone."""
        if cls is EntityType:
            return core_schema.no_info_after_validator_function(cls, core_schema.str_schema())
        return core_schema.no_info_after_validator_function(
            lambda _: cls(), core_schema.literal_schema([cls.name()])
        )


# Every entity doubles as a scope, so a scope type IS an entity type; the
# reverse direction stays an explicit declaration (`ScopeType(<entity type>)`).
ScopeType = NewType("ScopeType", EntityType)


class GlobalEntityType(EntityType):
    """The system itself, for a global operation that names nothing else. Wiring
    only — see `manager/actions/AGENTS.md`."""

    @override
    @classmethod
    def name(cls) -> str:
        return "global"

    @override
    @classmethod
    def description(cls) -> str:
        return "The system itself, recorded by a global operation that names no entity."


class FieldType(str):
    """The type of a field row.

    Kept apart from `EntityType` for the same reason that one is a class rather than a
    `NewType`: a field row is not an entity, and the two must not be interchangeable.

    Subclassed per kind the same way `EntityType` is, with the same rule for a value
    rebuilt from a string. A kind answers the entity kind owning its rows; a kind whose
    owner is a value on the row is a :class:`DanglingFieldType`.
    """

    def __new__(cls, value: str | None = None) -> Self:
        """A kind is built with no argument. Passing a value rebuilds the bare base from
        a string, which the rules below reserve for a boundary reading one."""
        return super().__new__(cls, cls.name() if value is None else value)

    @override
    def __reduce__(self) -> tuple[type[Any], tuple[Any, ...]]:
        if type(self) is FieldType:
            return (FieldType, (str(self),))
        return (type(self), ())

    @classmethod
    def name(cls) -> str:
        raise NotImplementedError

    @classmethod
    def description(cls) -> str:
        raise NotImplementedError

    @classmethod
    def owner_type(cls) -> type[EntityType] | None:
        """The entity kind owning this kind's rows, or ``None`` when the owner is a
        value on the row rather than one fixed kind."""
        raise NotImplementedError

    @classmethod
    def __get_pydantic_core_schema__(cls, source: Any, handler: GetCoreSchemaHandler) -> CoreSchema:
        """Validated as the string it is; pydantic builds no schema for a `str`
        subclass on its own. A kind accepts its own name alone."""
        if cls is FieldType:
            return core_schema.no_info_after_validator_function(cls, core_schema.str_schema())
        return core_schema.no_info_after_validator_function(
            lambda _: cls(), core_schema.literal_schema([cls.name()])
        )


class DanglingFieldType(FieldType):
    """A field kind whose owner is a value on the row, not one fixed entity kind."""

    @override
    @classmethod
    def owner_type(cls) -> None:
        return None


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


class EntityIdentifier(UUID):
    """An entity's id, which knows the type it is an id of.

    An id is the pair, not the uuid: two ids of different kinds carrying the same uuid
    are different ids, and a bare uuid is neither. That is what makes one usable as a
    key — a loader keyed by these reaches the same entry whether the caller named its
    kind statically or carried it as a value.
    """

    def __init__(self, value: UUID) -> None:
        super().__init__(int=value.int)

    @override
    def __eq__(self, other: object) -> bool:
        if not isinstance(other, EntityIdentifier):
            return NotImplemented
        return self.int == other.int and self.entity_type() == other.entity_type()

    @override
    def __hash__(self) -> int:
        """The uuid alone, as `UUID` hashes it.

        Two ids of different kinds carrying one uuid land in the same bucket and are
        told apart by ``__eq__`` there. Hashing the pair instead would put an id and
        the plain uuid a row answers with in different buckets, and a mapping keyed by
        one could not be read with the other.
        """
        return super().__hash__()

    @abstractmethod
    def entity_type(self) -> EntityType:
        """The type this is an id of.

        Read from the value, not the class: an id built from what a caller named carries
        its type instead of declaring one.
        """
        raise NotImplementedError

    @classmethod
    def __get_pydantic_core_schema__(cls, source: Any, handler: GetCoreSchemaHandler) -> CoreSchema:
        """Validated as the uuid it is; pydantic builds no schema for a `UUID`
        subclass on its own."""
        return core_schema.no_info_after_validator_function(cls, core_schema.uuid_schema())


class RuntimeEntityID(EntityIdentifier):
    """An entity id built from what a caller named, carrying its type as a value.

    For an input or a row that says which kind it is; where the kind is known statically,
    the declaring id class says so and this must not stand in for it.
    """

    _entity_type: EntityType

    def __init__(self, entity_type: EntityType, value: UUID) -> None:
        super().__init__(value)
        object.__setattr__(self, "_entity_type", entity_type)

    @override
    def entity_type(self) -> EntityType:
        return self._entity_type


class FieldIdentifier(UUID):
    """A field row's id.

    Names no entity: a field row carries no membership of its own, so what it belongs
    to is only knowable through the entity that owns it. Which entity that is comes from
    the owner lookup, not from this class: an owner may be another field row, and some
    kinds have none at all.
    """

    def __init__(self, value: UUID) -> None:
        super().__init__(int=value.int)

    @classmethod
    @abstractmethod
    def field_type(cls) -> FieldType:
        """Return the type of field row this id names."""
        raise NotImplementedError

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

    MUST carry the columns of its own domain's row and nothing else: no relationship,
    no joined value. Rationale: ``manager/data/KNOWLEDGE.md``.
    """

    @abstractmethod
    def entity_id(self) -> EntityIdentifier:
        """Return the id of the entity this value describes."""
        raise NotImplementedError


class FieldData(ABC):
    """A ``data/`` type describing a field row.

    Deliberately not an :class:`EntityData`: a field row carries no membership of its
    own, so what a result names is the entity owning it, not the row. The owning entity
    is read by the lookup every field operation runs first, not off this value.

    MUST carry the columns of its own domain's row and nothing else: no relationship,
    no joined value. Rationale: ``manager/data/KNOWLEDGE.md``.
    """
