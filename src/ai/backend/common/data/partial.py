"""Records that hold the fields a request selected.

A subclass of `PartialRecord` declares its fields as annotations. A field assigned
`selectable()` may be left out of the constructor; reading it then raises
`NotSelectedError`. `None` stays a value (a NULL), never "not selected".
"""

from __future__ import annotations

import inspect
from collections.abc import Callable, Mapping
from typing import TYPE_CHECKING, Any, ClassVar, dataclass_transform, final, override

from ai.backend.common.errors.partial_record import (
    FrozenPartialRecordError,
    InvalidPartialRecordError,
    NotSelectedError,
)
from ai.backend.common.tristate.unset import UNSET, Unset


@final
class _SelectableMarker:
    pass


def selectable() -> Any:
    """Mark a field of a `PartialRecord` as one a request may leave out."""
    return _SelectableMarker()


@dataclass_transform(frozen_default=True, kw_only_default=True)
class PartialRecord:
    _record_fields: ClassVar[tuple[str, ...]] = ()
    _selectable_fields: ClassVar[frozenset[str]] = frozenset()
    _declared_fields: ClassVar[frozenset[str]] = frozenset()
    _required_fields: ClassVar[frozenset[str]] = frozenset()

    @override
    def __init_subclass__(cls, **kwargs: Any) -> None:
        super().__init_subclass__(**kwargs)
        fields = list(cls._record_fields)
        selectables = set(cls._selectable_fields)
        for name in inspect.get_annotations(cls):
            value = cls.__dict__.get(name)
            if isinstance(value, _SelectableMarker):
                selectables.add(name)
                delattr(cls, name)
            elif name in cls.__dict__:
                raise InvalidPartialRecordError(
                    f"{cls.__name__}.{name}: only selectable() can stand in a field default"
                )
            if name not in fields:
                fields.append(name)
        cls._record_fields = tuple(fields)
        cls._selectable_fields = frozenset(selectables)
        cls._declared_fields = frozenset(fields)
        cls._required_fields = cls._declared_fields - cls._selectable_fields

    def __init__(self, **values: Any) -> None:
        cls = type(self)
        names = values.keys()
        if not names <= cls._declared_fields:
            raise InvalidPartialRecordError(
                f"{cls.__name__}: undeclared fields {sorted(names - cls._declared_fields)}"
            )
        if not cls._required_fields <= names:
            raise InvalidPartialRecordError(
                f"{cls.__name__}: missing required fields {sorted(cls._required_fields - names)}"
            )
        self.__dict__.update(values)

    if not TYPE_CHECKING:
        # Hidden from type checkers so that an undeclared name stays an error.

        def __getattr__(self, name: str) -> Any:
            if name in type(self)._selectable_fields:
                raise NotSelectedError(f"{type(self).__name__}.{name} was not selected")
            raise AttributeError(name)

    @override
    def __setattr__(self, name: str, value: Any) -> None:
        raise FrozenPartialRecordError(f"{type(self).__name__}.{name} cannot be assigned")

    @override
    def __delattr__(self, name: str) -> None:
        raise FrozenPartialRecordError(f"{type(self).__name__}.{name} cannot be deleted")

    def or_missing[T](self, read: Callable[[], T]) -> T | Unset:
        """Return what ``read`` reads from this record, or pydantic ``MISSING`` if not selected."""
        try:
            return read()
        except NotSelectedError:
            return UNSET

    def is_selected(self, name: str) -> bool:
        return name in self.__dict__

    def selected_fields(self) -> tuple[str, ...]:
        """Selected field names in declaration order."""
        return tuple(name for name in type(self)._record_fields if name in self.__dict__)

    def _selected_values(self) -> Mapping[str, Any]:
        return {name: self.__dict__[name] for name in self.selected_fields()}

    @override
    def __eq__(self, other: object) -> bool:
        if not isinstance(other, PartialRecord) or type(other) is not type(self):
            return NotImplemented
        return self._selected_values() == other._selected_values()

    @override
    def __hash__(self) -> int:
        return hash((type(self), tuple(self._selected_values().items())))

    @override
    def __repr__(self) -> str:
        values = ", ".join(f"{name}={value!r}" for name, value in self._selected_values().items())
        return f"{type(self).__name__}({values})"
