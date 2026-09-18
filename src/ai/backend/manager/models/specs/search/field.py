"""One field of an entity, with what it can be filtered and ordered by."""

from __future__ import annotations

from dataclasses import dataclass
from typing import Any

from ai.backend.manager.models.specs.conditions.boolean import BoolConditions
from ai.backend.manager.models.specs.conditions.datetime import DateTimeConditions
from ai.backend.manager.models.specs.conditions.enum import EnumConditions
from ai.backend.manager.models.specs.conditions.integer import IntConditions
from ai.backend.manager.models.specs.conditions.string import StringConditions
from ai.backend.manager.models.specs.conditions.uuid import UUIDConditions
from ai.backend.manager.models.specs.orders.base import SearchOrder

type FieldConditions = (
    StringConditions
    | UUIDConditions
    | DateTimeConditions
    | IntConditions
    | EnumConditions[Any]
    | BoolConditions
)


@dataclass(frozen=True)
class SearchableField[F: FieldConditions | None, O: SearchOrder | None]:
    """A ``None`` slot says the field cannot be filtered, or ordered, by."""

    filter: F
    order: O
