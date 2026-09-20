"""One field of an entity, with what it can be filtered and ordered by."""

from __future__ import annotations

from dataclasses import dataclass
from typing import Any

from sqlalchemy.orm import InstrumentedAttribute

from ai.backend.manager.models.specs.conditions.boolean import BoolConditions
from ai.backend.manager.models.specs.conditions.datetime import DateTimeConditions
from ai.backend.manager.models.specs.conditions.enum import EnumConditions
from ai.backend.manager.models.specs.conditions.integer import IntConditions
from ai.backend.manager.models.specs.conditions.number import (
    DecimalConditions,
    FloatConditions,
)
from ai.backend.manager.models.specs.conditions.string import StringConditions
from ai.backend.manager.models.specs.conditions.uuid import UUIDConditions
from ai.backend.manager.models.specs.orders.base import SearchOrder
from ai.backend.manager.models.specs.search.correlation import ToManyCorrelation, ToOneCorrelation

type FieldConditions = (
    StringConditions
    | UUIDConditions
    | DateTimeConditions
    | IntConditions
    | FloatConditions
    | DecimalConditions
    | EnumConditions[Any]
    | BoolConditions
)


@dataclass(frozen=True)
class SearchableField[V, F: FieldConditions | None, O: SearchOrder | None]:
    """One column: how it is read, filtered and ordered. A ``None`` slot says it cannot be."""

    column: InstrumentedAttribute[V]
    filter: F
    order: O

    def read(self, row: object) -> V:
        return self.column.__get__(row, type(row))


@dataclass(frozen=True)
class NestedSearchableField[TFields, C: ToManyCorrelation | ToOneCorrelation]:
    """Fields of another table, reached from this entity through ``correlation``."""

    fields: TFields
    correlation: C
