"""Every entity and field type class answers its name, description and owner."""

from __future__ import annotations

import copy
import importlib
import pickle
import pkgutil
from typing import override

import pytest
from pydantic import TypeAdapter, ValidationError

import ai.backend.common.data.entity as entity_package
from ai.backend.common.data.entity.agent import AgentEntityType
from ai.backend.common.data.entity.types import (
    DanglingFieldType,
    DeclaredEntityType,
    EntityType,
    FieldType,
)
from ai.backend.common.data.entity.vfolder import VFolderEntityType
from ai.backend.common.exception import DuplicateEntityTypeName


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


@pytest.mark.parametrize("value", ["vfolder", "VFOLDER", "Vfolder"])
def test_declared_entity_type_accepts_a_declared_name_ignoring_case(value: str) -> None:
    resolved = TypeAdapter(DeclaredEntityType).validate_python(value)
    assert type(resolved) is VFolderEntityType


@pytest.mark.parametrize(
    "value",
    ["model_deployment", "vfolder:data", "deployment:token", "storage_host", "routing"],
)
def test_declared_entity_type_refuses_an_undeclared_name(value: str) -> None:
    with pytest.raises(ValidationError):
        TypeAdapter(DeclaredEntityType).validate_python(value)


def test_kind_differing_from_a_registered_name_only_in_case_is_refused() -> None:
    with pytest.raises(DuplicateEntityTypeName):

        class UpperVFolderEntityType(EntityType):
            __module__ = f"{entity_package.__name__}.fake"

            @override
            @classmethod
            def name(cls) -> str:
                return "VFOLDER"
