"""The data fields a GQL request selected on a node type.

GQL selection names stay in this module; adapters receive ``RequestedFields``.
"""

from __future__ import annotations

from collections.abc import Iterable, Iterator, Mapping, Sequence
from typing import Any, ClassVar

from strawberry import Info
from strawberry.types.base import StrawberryObjectDefinition, get_object_definition
from strawberry.types.field import StrawberryField
from strawberry.types.nodes import FragmentSpread, InlineFragment, SelectedField, Selection

from ai.backend.manager.api.adapter_options.requested_fields.requested_fields import (
    RequestedFields,
)
from ai.backend.manager.api.gql.pydantic_compat import PydanticNodeMixin
from ai.backend.manager.errors.api import InvalidResolverReads, RequestedFieldNotDeclared


class ResolverReads:
    """The plain fields of its own type a resolver field reads its value from."""

    _METADATA_KEY: ClassVar[str] = "backendai_resolver_reads"

    fields: tuple[StrawberryField, ...]

    def __init__(self, fields: Sequence[object]) -> None:
        # Typed `object`: mypy reads a field name in a class body as the field's value type.
        plain: list[StrawberryField] = []
        for field in fields:
            if not isinstance(field, StrawberryField) or field.base_resolver is not None:
                raise InvalidResolverReads(f"reads takes plain fields only, not {field!r}")
            plain.append(field)
        self.fields = tuple(plain)

    def as_metadata(self) -> dict[str, Any]:
        return {self._METADATA_KEY: self}

    @classmethod
    def of(cls, field: StrawberryField) -> ResolverReads | None:
        value = field.metadata.get(cls._METADATA_KEY)
        return value if isinstance(value, ResolverReads) else None


class RequestedFieldReader:
    """Maps the selection of the current GQL field to the data field names of a node type.

    A plain field maps to its Python name, the relay ``id`` and ``entity_id`` to ``id``,
    and a resolver field to the fields its ``reads`` names; a resolver without it adds none.
    """

    _ID_FIELDS: ClassVar[frozenset[str]] = frozenset({"_id", "entity_id"})
    _DATA_ID: ClassVar[str] = "id"
    _EDGES: ClassVar[str] = "edges"
    _NODE: ClassVar[str] = "node"

    _info: Info[Any, Any]

    def __init__(self, info: Info[Any, Any]) -> None:
        self._info = info

    def node_fields(self, node_class: type[PydanticNodeMixin[Any]]) -> RequestedFields:
        """For a field returning the node itself."""
        return self._requested(node_class, self._current_selections())

    def connection_node_fields(self, node_class: type[PydanticNodeMixin[Any]]) -> RequestedFields:
        """For a field returning a connection of the node: the selection under ``edges.node``."""
        edges = self._children(self._current_selections(), self._EDGES)
        return self._requested(node_class, self._children(edges, self._NODE))

    def _current_selections(self) -> list[Selection]:
        return [
            selection
            for current in self._info.selected_fields
            if isinstance(current, SelectedField)
            for selection in current.selections
        ]

    def _children(self, selections: Iterable[Selection], name: str) -> list[Selection]:
        return [
            child
            for selected in self._flatten(selections)
            if selected.name == name
            for child in selected.selections
        ]

    def _flatten(self, selections: Iterable[Selection]) -> Iterator[SelectedField]:
        """Selected fields with fragment spreads and inline fragments expanded."""
        for selection in selections:
            if isinstance(selection, SelectedField):
                yield selection
            elif isinstance(selection, (FragmentSpread, InlineFragment)):
                yield from self._flatten(selection.selections)

    def _requested(
        self, node_class: type[PydanticNodeMixin[Any]], selections: Iterable[Selection]
    ) -> RequestedFields:
        definition = get_object_definition(node_class, strict=True)
        by_graphql_name = self._fields_by_graphql_name(definition)
        names: set[str] = set()
        for selected in self._flatten(selections):
            if selected.name.startswith("__"):
                continue
            field = by_graphql_name.get(selected.name)
            if field is None:
                raise RequestedFieldNotDeclared(f"{definition.name} has no field {selected.name}")
            names.update(self._data_names(definition, field))
        return RequestedFields(names=frozenset(names))

    def _fields_by_graphql_name(
        self, definition: StrawberryObjectDefinition
    ) -> Mapping[str, StrawberryField]:
        converter = self._info.schema.config.name_converter
        by_name: dict[str, StrawberryField] = {}
        for field in definition.fields:
            # The relay `id` resolver is listed before the `NodeID` field it shadows.
            by_name.setdefault(converter.get_graphql_name(field), field)
        return by_name

    def _data_names(
        self, definition: StrawberryObjectDefinition, field: StrawberryField
    ) -> tuple[str, ...]:
        if field.python_name in self._ID_FIELDS:
            return (self._DATA_ID,)
        if field.base_resolver is None:
            return (field.python_name,)
        reads = ResolverReads.of(field)
        if reads is None:
            return ()
        names: list[str] = []
        for read in reads.fields:
            if not any(read is declared for declared in definition.fields):
                raise InvalidResolverReads(
                    f"{definition.name}.{field.python_name} reads a field of another type"
                )
            names.extend(self._data_names(definition, read))
        return tuple(names)
