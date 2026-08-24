"""Query conditions and orders for labels, and the nested-filter builder every
labelable entity reuses."""

from __future__ import annotations

from collections.abc import Callable
from dataclasses import dataclass
from typing import Any

import sqlalchemy as sa
from sqlalchemy.orm import InstrumentedAttribute

from ai.backend.common.data.entity.types import EntityType
from ai.backend.common.data.filter_specs import (
    StringMatchSpec,
    UUIDEqualMatchSpec,
    UUIDInMatchSpec,
)
from ai.backend.manager.models.clauses import QueryCondition, QueryOrder
from ai.backend.manager.models.condition_utils import (
    make_correlated_exists,
    make_string_in_factory,
    negate_conditions,
)
from ai.backend.manager.models.label.row import LabelRow

__all__ = (
    "LabelConditions",
    "LabelNestedConditions",
    "LabelOrders",
    "make_label_nested_conditions",
)

type LabelConditionFactory = Callable[[list[QueryCondition]], QueryCondition]


@dataclass(frozen=True)
class LabelNestedConditions:
    """The three set relations a labelable entity's ``labels`` filter offers.

    Each takes the conditions matching a single label row, so ``key`` and ``value``
    constrain the same label rather than two different ones.
    """

    some: LabelConditionFactory
    """At least one of the entity's labels matches."""

    every: LabelConditionFactory
    """All of them match; vacuously true for an unlabeled entity."""

    none: LabelConditionFactory
    """None of them matches."""


def make_label_nested_conditions(
    correlate_row: type[Any],
    entity_id_column: InstrumentedAttribute[Any],
    entity_type: EntityType,
) -> LabelNestedConditions:
    """Build the ``labels`` nested-filter conditions for one labelable entity.

    Each relation compiles to a correlated ``EXISTS`` over the label table against the
    entity row, with the label predicates inside it.
    """
    exists = make_correlated_exists(
        child_row=LabelRow,
        correlate_row=correlate_row,
        join_predicate=sa.and_(
            LabelRow.entity_id == entity_id_column,
            LabelRow.entity_type == entity_type,
        ),
    )

    def negated(factory: LabelConditionFactory) -> LabelConditionFactory:
        def outer(child_conditions: list[QueryCondition]) -> QueryCondition:
            condition = factory(child_conditions)

            def inner() -> sa.sql.expression.ColumnElement[bool]:
                return sa.not_(condition())

            return inner

        return outer

    def every(child_conditions: list[QueryCondition]) -> QueryCondition:
        return negated(exists)([negate_conditions(child_conditions)])

    return LabelNestedConditions(some=exists, every=every, none=negated(exists))


class LabelConditions:
    """Query conditions for labels."""

    # --- key string filters ---

    @staticmethod
    def by_key_equals(spec: StringMatchSpec) -> QueryCondition:
        def inner() -> sa.sql.expression.ColumnElement[bool]:
            if spec.case_insensitive:
                condition = sa.func.lower(LabelRow.key) == spec.value.lower()
            else:
                condition = LabelRow.key == spec.value
            if spec.negated:
                condition = sa.not_(condition)
            return condition

        return inner

    @staticmethod
    def by_key_contains(spec: StringMatchSpec) -> QueryCondition:
        def inner() -> sa.sql.expression.ColumnElement[bool]:
            if spec.case_insensitive:
                condition = LabelRow.key.ilike(f"%{spec.value}%")
            else:
                condition = LabelRow.key.like(f"%{spec.value}%")
            if spec.negated:
                condition = sa.not_(condition)
            return condition

        return inner

    @staticmethod
    def by_key_starts_with(spec: StringMatchSpec) -> QueryCondition:
        def inner() -> sa.sql.expression.ColumnElement[bool]:
            if spec.case_insensitive:
                condition = LabelRow.key.ilike(f"{spec.value}%")
            else:
                condition = LabelRow.key.like(f"{spec.value}%")
            if spec.negated:
                condition = sa.not_(condition)
            return condition

        return inner

    @staticmethod
    def by_key_ends_with(spec: StringMatchSpec) -> QueryCondition:
        def inner() -> sa.sql.expression.ColumnElement[bool]:
            if spec.case_insensitive:
                condition = LabelRow.key.ilike(f"%{spec.value}")
            else:
                condition = LabelRow.key.like(f"%{spec.value}")
            if spec.negated:
                condition = sa.not_(condition)
            return condition

        return inner

    by_key_in = staticmethod(make_string_in_factory(LabelRow.key))

    # --- value string filters ---

    @staticmethod
    def by_value_equals(spec: StringMatchSpec) -> QueryCondition:
        def inner() -> sa.sql.expression.ColumnElement[bool]:
            if spec.case_insensitive:
                condition = sa.func.lower(LabelRow.value) == spec.value.lower()
            else:
                condition = LabelRow.value == spec.value
            if spec.negated:
                condition = sa.not_(condition)
            return condition

        return inner

    @staticmethod
    def by_value_contains(spec: StringMatchSpec) -> QueryCondition:
        def inner() -> sa.sql.expression.ColumnElement[bool]:
            if spec.case_insensitive:
                condition = LabelRow.value.ilike(f"%{spec.value}%")
            else:
                condition = LabelRow.value.like(f"%{spec.value}%")
            if spec.negated:
                condition = sa.not_(condition)
            return condition

        return inner

    @staticmethod
    def by_value_starts_with(spec: StringMatchSpec) -> QueryCondition:
        def inner() -> sa.sql.expression.ColumnElement[bool]:
            if spec.case_insensitive:
                condition = LabelRow.value.ilike(f"{spec.value}%")
            else:
                condition = LabelRow.value.like(f"{spec.value}%")
            if spec.negated:
                condition = sa.not_(condition)
            return condition

        return inner

    @staticmethod
    def by_value_ends_with(spec: StringMatchSpec) -> QueryCondition:
        def inner() -> sa.sql.expression.ColumnElement[bool]:
            if spec.case_insensitive:
                condition = LabelRow.value.ilike(f"%{spec.value}")
            else:
                condition = LabelRow.value.like(f"%{spec.value}")
            if spec.negated:
                condition = sa.not_(condition)
            return condition

        return inner

    by_value_in = staticmethod(make_string_in_factory(LabelRow.value))

    # --- entity_type string filters ---

    @staticmethod
    def by_entity_type_equals(spec: StringMatchSpec) -> QueryCondition:
        def inner() -> sa.sql.expression.ColumnElement[bool]:
            if spec.case_insensitive:
                condition = sa.func.lower(LabelRow.entity_type) == spec.value.lower()
            else:
                condition = LabelRow.entity_type == spec.value
            if spec.negated:
                condition = sa.not_(condition)
            return condition

        return inner

    by_entity_type_in = staticmethod(make_string_in_factory(LabelRow.entity_type))

    # --- entity_id UUID filters ---

    @staticmethod
    def by_entity_id_equals(spec: UUIDEqualMatchSpec) -> QueryCondition:
        def inner() -> sa.sql.expression.ColumnElement[bool]:
            condition = LabelRow.entity_id == spec.value
            if spec.negated:
                condition = sa.not_(condition)
            return condition

        return inner

    @staticmethod
    def by_entity_id_in(spec: UUIDInMatchSpec) -> QueryCondition:
        def inner() -> sa.sql.expression.ColumnElement[bool]:
            condition = LabelRow.entity_id.in_(spec.values)
            if spec.negated:
                condition = sa.not_(condition)
            return condition

        return inner

    # --- cursor pagination conditions ---

    @staticmethod
    def by_cursor_forward(cursor_id: str) -> QueryCondition:
        def inner() -> sa.sql.expression.ColumnElement[bool]:
            subquery = (
                sa.select(LabelRow.created_at).where(LabelRow.id == cursor_id).scalar_subquery()
            )
            return LabelRow.created_at < subquery

        return inner

    @staticmethod
    def by_cursor_backward(cursor_id: str) -> QueryCondition:
        def inner() -> sa.sql.expression.ColumnElement[bool]:
            subquery = (
                sa.select(LabelRow.created_at).where(LabelRow.id == cursor_id).scalar_subquery()
            )
            return LabelRow.created_at > subquery

        return inner


class LabelOrders:
    """Query orders for labels."""

    @staticmethod
    def key(ascending: bool = True) -> QueryOrder:
        if ascending:
            return LabelRow.key.asc()
        return LabelRow.key.desc()

    @staticmethod
    def value(ascending: bool = True) -> QueryOrder:
        if ascending:
            return LabelRow.value.asc()
        return LabelRow.value.desc()

    @staticmethod
    def created_at(ascending: bool = True) -> QueryOrder:
        if ascending:
            return LabelRow.created_at.asc()
        return LabelRow.created_at.desc()
