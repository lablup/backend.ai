"""Every entity and field type class answers its name, description and owner."""

from __future__ import annotations

import copy
import importlib
import pickle
import pkgutil

import pytest
from pydantic import TypeAdapter, ValidationError

import ai.backend.common.data.entity as entity_package
from ai.backend.common.data.entity.agent import AgentEntityType
from ai.backend.common.data.entity.types import DanglingFieldType, EntityType, FieldType


def _subclasses[T: type](base: T) -> list[T]:
    found: list[T] = []
    for sub in base.__subclasses__():
        found.append(sub)
        found.extend(_subclasses(sub))
    return found


def _load_package() -> None:
    for module in pkgutil.iter_modules(entity_package.__path__):
        importlib.import_module(f"{entity_package.__name__}.{module.name}")


_load_package()
ENTITY_TYPES = _subclasses(EntityType)
FIELD_TYPES = [cls for cls in _subclasses(FieldType) if cls is not DanglingFieldType]


@pytest.mark.parametrize("cls", [*ENTITY_TYPES, *FIELD_TYPES], ids=lambda cls: cls.__name__)
def test_type_class_answers_its_value(cls: type[EntityType] | type[FieldType]) -> None:
    value = cls()
    assert type(value) is cls
    assert value == cls.name()
    assert cls.description()
    assert type(copy.deepcopy(value)) is cls
    assert type(pickle.loads(pickle.dumps(value))) is cls


@pytest.mark.parametrize("cls", FIELD_TYPES, ids=lambda cls: cls.__name__)
def test_field_type_names_its_owner(cls: type[FieldType]) -> None:
    owner = cls.owner_type()
    if issubclass(cls, DanglingFieldType):
        assert owner is None
    else:
        assert owner in ENTITY_TYPES


def test_names_are_unique_per_kind() -> None:
    entity_names = [cls.name() for cls in ENTITY_TYPES]
    field_names = [cls.name() for cls in FIELD_TYPES]
    assert len(entity_names) == len(set(entity_names))
    assert len(field_names) == len(set(field_names))


def test_pydantic_keeps_a_kind_and_accepts_its_name_alone() -> None:
    assert type(TypeAdapter(AgentEntityType).validate_python("agent")) is AgentEntityType
    with pytest.raises(ValidationError):
        TypeAdapter(AgentEntityType).validate_python("user")


def test_value_rebuilt_from_a_string_is_a_bare_base() -> None:
    rebuilt = EntityType("agent")
    assert type(rebuilt) is EntityType
    assert rebuilt == "agent"
    assert type(pickle.loads(pickle.dumps(rebuilt))) is EntityType
    with pytest.raises(NotImplementedError):
        rebuilt.name()
