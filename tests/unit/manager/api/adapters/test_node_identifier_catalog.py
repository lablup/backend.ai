"""The adapter catalog vs the identifier every response node has to carry.

``Adapters.__init__`` names every adapter the application wires, and each adapter's
data-to-node conversions say which ``data/`` type a node is built from. A node built
from an :class:`EntityData` must carry ``entity_id``; one built from a
:class:`FieldData` must carry ``field_id``. The GQL sweep holds the node types
declared over those DTOs to the same field, so a client reads the same identifier
through either surface.
"""

from __future__ import annotations

import inspect
import sys
import typing
from typing import Any, NamedTuple, override

from ai.backend.common.api_handlers import BaseResponseModel
from ai.backend.common.data.entity.types import EntityData, FieldData
from ai.backend.manager.api.adapters.registry import Adapters
from ai.backend.manager.api.gql.pydantic_compat import PydanticNodeMixin
from ai.backend.manager.api.gql.schema import schema as _gql_schema

assert _gql_schema is not None, "the GQL schema is built so every node type is defined"

ENTITY_ID = "entity_id"
FIELD_ID = "field_id"

# Rows whose ``data/`` type holds no id of its own, so no node built from one can name
# a row. The fair share values are computed per (resource group, scope) pair and the
# allocation rows per (kernel, slot name); neither is stored under a row id.
_ROWS_WITHOUT_AN_ID = frozenset({
    "DomainFairShareData",
    "ProjectFairShareData",
    "UserFairShareData",
    "ResourceAllocationData",
})


class _Conversion(NamedTuple):
    adapter: str
    method: str
    node: type[BaseResponseModel]
    data: str
    expected_field: str

    @override
    def __str__(self) -> str:
        return (
            f"{self.adapter}.{self.method} builds {self.node.__name__} from {self.data}, "
            f"which has to carry {self.expected_field}"
        )


def _adapter_classes() -> list[type[Any]]:
    return [
        cls for name, cls in typing.get_type_hints(Adapters.__init__).items() if name != "return"
    ]


def _plain_function(cls: type[Any], name: str) -> Any:
    raw = inspect.getattr_static(cls, name)
    if isinstance(raw, (classmethod, staticmethod)):
        return raw.__func__
    return raw if inspect.isfunction(raw) else None


def _returned_node(fn: Any) -> type[BaseResponseModel] | None:
    """The response node a conversion returns, read off its return annotation alone.

    Only the return is resolved here: a conversion's own module may not be able to
    resolve every parameter annotation at runtime, and a method returning something
    else is not a conversion to judge.
    """
    annotation = fn.__annotations__.get("return")
    if not isinstance(annotation, str):
        return None
    try:
        returned = eval(annotation, sys.modules[fn.__module__].__dict__)
    except Exception:
        return None
    if not isinstance(returned, type) or not issubclass(returned, BaseResponseModel):
        return None
    return returned if returned.__name__.endswith("Node") else None


def _conversions() -> list[_Conversion]:
    found: dict[tuple[str, str, str], _Conversion] = {}
    for cls in _adapter_classes():
        for name in dir(cls):
            fn = _plain_function(cls, name)
            if fn is None:
                continue
            node = _returned_node(fn)
            if node is None:
                continue
            hints = typing.get_type_hints(fn)
            hints.pop("return", None)
            for annotation in hints.values():
                if not isinstance(annotation, type):
                    continue
                if annotation.__name__ in _ROWS_WITHOUT_AN_ID:
                    continue
                if issubclass(annotation, EntityData):
                    expected = ENTITY_ID
                elif issubclass(annotation, FieldData):
                    expected = FIELD_ID
                else:
                    continue
                conversion = _Conversion(cls.__name__, name, node, annotation.__name__, expected)
                found[(cls.__name__, name, annotation.__name__)] = conversion
    return sorted(found.values())


def test_every_adapter_is_a_class_the_catalog_names() -> None:
    """The sweep reads the catalog, so an adapter missing from it is swept over."""
    adapters = _adapter_classes()
    assert adapters
    assert all(isinstance(cls, type) for cls in adapters)


def test_nodes_built_from_a_row_carry_that_row_s_identifier() -> None:
    missing = [
        conversion
        for conversion in _conversions()
        if conversion.expected_field not in conversion.node.model_fields
    ]
    assert not missing, "response nodes missing their identifier:\n" + "\n".join(
        f"  {conversion}" for conversion in missing
    )


def _node_types() -> list[type[Any]]:
    found: list[type[Any]] = []
    pending = [PydanticNodeMixin]
    while pending:
        for subclass in pending.pop().__subclasses__():
            found.append(subclass)
            pending.append(subclass)
    return found


def _declared_model(cls: type[Any]) -> type[BaseResponseModel] | None:
    for base in getattr(cls, "__orig_bases__", ()):
        if typing.get_origin(base) is not PydanticNodeMixin:
            continue
        (model,) = typing.get_args(base)
        if isinstance(model, type) and issubclass(model, BaseResponseModel):
            return model
    return None


# GQL node types that name no DTO, so the sweep below cannot hold them to one. Each
# projects values a resolver assembles rather than mapping one response node.
_NODE_TYPES_OVER_NO_DTO = frozenset({
    "EntityRefGQL",
    "KernelResourceAllocationGQL",
    "RoleInvitationGQL",
})


def test_gql_node_types_name_the_dto_they_map() -> None:
    """A node type parameterised on ``Any`` drops out of the sweep below unnoticed."""
    loose = sorted(
        cls.__name__
        for cls in _node_types()
        if _declared_model(cls) is None and cls.__name__ not in _NODE_TYPES_OVER_NO_DTO
    )
    assert not loose, (
        "GQL node types that name no response node, so nothing holds them to its "
        f"identifier: {loose}"
    )


def test_gql_node_types_declare_the_identifier_their_dto_carries() -> None:
    missing: list[str] = []
    for cls in _node_types():
        model = _declared_model(cls)
        if model is None:
            continue
        declared = {field.name for field in _strawberry_fields(cls)}
        for name in (ENTITY_ID, FIELD_ID):
            if name in model.model_fields and name not in declared:
                missing.append(f"  {cls.__name__} over {model.__name__} does not declare {name}")
    assert not missing, "GQL node types missing their identifier:\n" + "\n".join(missing)


def _strawberry_fields(cls: type[Any]) -> list[Any]:
    definition = getattr(cls, "__strawberry_definition__", None)
    return list(definition.fields) if definition is not None else []
