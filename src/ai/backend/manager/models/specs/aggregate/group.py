"""What an aggregate can group by: the per-field declarations and the groups a request asks for."""

from __future__ import annotations

import uuid
from abc import ABC, abstractmethod
from collections.abc import Sequence
from dataclasses import dataclass
from datetime import datetime, timedelta
from enum import Enum
from typing import Any, override
from zoneinfo import ZoneInfo

import sqlalchemy as sa

from ai.backend.manager.models.specs.search.field import SearchableField

__all__ = (
    "DateTimeBucket",
    "DateTimeGroupBy",
    "DateTimeGroupField",
    "EnumGroupBy",
    "EnumGroupField",
    "GroupBy",
    "StringGroupBy",
    "StringGroupField",
    "UUIDGroupBy",
    "UUIDGroupField",
)


@dataclass(frozen=True)
class DateTimeBucket:
    """The half-open range ``[start, end)`` one datetime group covers."""

    start: datetime
    end: datetime


class GroupBy(ABC):
    """One group a request asks for: the SQL expression grouped and how a key is read back."""

    @abstractmethod
    def expression(self) -> sa.ColumnElement[Any]:
        """The expression the rows are grouped by."""
        raise NotImplementedError

    @abstractmethod
    def to_key(self, value: Any) -> Any:
        """The group key the result carries for one grouped value."""
        raise NotImplementedError

    @abstractmethod
    def include_null(self) -> bool:
        """Whether the rows whose value is NULL form a group of their own."""
        raise NotImplementedError

    @abstractmethod
    def empty_values(self) -> Sequence[Any]:
        """The values answered with a zero count when no row has them."""
        raise NotImplementedError


@dataclass(frozen=True, eq=False)
class EnumGroupBy[E: Enum](GroupBy):
    column: sa.ColumnElement[E]
    enum_cls: type[E]
    include_empty: bool

    @override
    def expression(self) -> sa.ColumnElement[Any]:
        return self.column

    @override
    def to_key(self, value: Any) -> Any:
        return value

    @override
    def include_null(self) -> bool:
        return False

    @override
    def empty_values(self) -> Sequence[Any]:
        return list(self.enum_cls) if self.include_empty else ()


@dataclass(frozen=True, eq=False)
class DateTimeGroupBy(GroupBy):
    """Fixed-length buckets of ``interval``, aligned to midnight in ``timezone``."""

    column: sa.ColumnElement[datetime]
    interval: timedelta
    timezone: ZoneInfo

    @override
    def expression(self) -> sa.ColumnElement[Any]:
        # A Monday at midnight: day buckets start at midnight, week buckets on Monday.
        origin = datetime(2001, 1, 1, tzinfo=self.timezone)
        return sa.func.date_bin(
            sa.literal(self.interval, sa.Interval()),
            self.column,
            sa.literal(origin, sa.DateTime(timezone=True)),
            type_=sa.DateTime(timezone=True),
        )

    @override
    def to_key(self, value: Any) -> Any:
        if value is None:
            return None
        return DateTimeBucket(start=value, end=value + self.interval)

    @override
    def include_null(self) -> bool:
        return False

    @override
    def empty_values(self) -> Sequence[Any]:
        return ()


@dataclass(frozen=True, eq=False)
class UUIDGroupBy(GroupBy):
    column: sa.ColumnElement[uuid.UUID]
    with_null: bool

    @override
    def expression(self) -> sa.ColumnElement[Any]:
        return self.column

    @override
    def to_key(self, value: Any) -> Any:
        return value

    @override
    def include_null(self) -> bool:
        return self.with_null

    @override
    def empty_values(self) -> Sequence[Any]:
        return ()


@dataclass(frozen=True, eq=False)
class StringGroupBy(GroupBy):
    column: sa.ColumnElement[Any]
    with_null: bool

    @override
    def expression(self) -> sa.ColumnElement[Any]:
        return self.column

    @override
    def to_key(self, value: Any) -> Any:
        return None if value is None else str(value)

    @override
    def include_null(self) -> bool:
        return self.with_null

    @override
    def empty_values(self) -> Sequence[Any]:
        return ()


@dataclass(frozen=True)
class EnumGroupField[E: Enum]:
    """A field that groups by its enum values."""

    field: SearchableField[Any, Any, Any]
    enum_cls: type[E]

    def by(self, *, include_empty: bool) -> EnumGroupBy[E]:
        return EnumGroupBy(self.field.column.expression, self.enum_cls, include_empty)


@dataclass(frozen=True)
class DateTimeGroupField:
    """A field that groups by fixed-length time buckets."""

    field: SearchableField[Any, Any, Any]

    def by(self, *, interval: timedelta, timezone: ZoneInfo) -> DateTimeGroupBy:
        return DateTimeGroupBy(self.field.column.expression, interval, timezone)


@dataclass(frozen=True)
class UUIDGroupField:
    """A field that groups by its UUID values."""

    field: SearchableField[Any, Any, Any]

    def by(self, *, include_null: bool) -> UUIDGroupBy:
        return UUIDGroupBy(self.field.column.expression, include_null)


@dataclass(frozen=True)
class StringGroupField:
    """A field that groups by its string values."""

    field: SearchableField[Any, Any, Any]

    def by(self, *, include_null: bool) -> StringGroupBy:
        return StringGroupBy(self.field.column.expression, include_null)
