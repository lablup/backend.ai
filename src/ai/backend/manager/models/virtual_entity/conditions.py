"""Query conditions over the scope side of a virtual-entity membership edge.

The counterpart of the association-table conditions for reads that follow
``scope -> virtual entity -> entity``. They read :class:`VirtualEntityRow`, which
:func:`~ai.backend.manager.models.virtual_entity.queries.owning_scope_exists` joins as
the scope side.
"""

from __future__ import annotations

from collections.abc import Collection

import sqlalchemy as sa

from ai.backend.common.data.entity.types import EntityID, EntityType
from ai.backend.common.data.filter_specs import StringInMatchSpec, StringMatchSpec
from ai.backend.manager.models.clauses import QueryCondition
from ai.backend.manager.models.virtual_entity.virtual_entity import VirtualEntityRow

__all__ = ("OwningScopeConditions",)


def _scope_id_text() -> sa.sql.expression.ColumnElement[str]:
    """The scope's id as text: the column is a uuid and the filters match substrings."""
    return sa.cast(VirtualEntityRow.entity_id, sa.String)


class OwningScopeConditions:
    """Query conditions for the scope owning an entity."""

    @staticmethod
    def by_scope_type_equals(scope_type: EntityType) -> QueryCondition:
        def inner() -> sa.sql.expression.ColumnElement[bool]:
            return VirtualEntityRow.entity_type == scope_type

        return inner

    @staticmethod
    def by_scope_type_not_equals(scope_type: EntityType) -> QueryCondition:
        def inner() -> sa.sql.expression.ColumnElement[bool]:
            return VirtualEntityRow.entity_type != scope_type

        return inner

    @staticmethod
    def by_scope_type_in(scope_types: Collection[EntityType]) -> QueryCondition:
        def inner() -> sa.sql.expression.ColumnElement[bool]:
            return VirtualEntityRow.entity_type.in_(list(scope_types))

        return inner

    @staticmethod
    def by_scope_type_not_in(scope_types: Collection[EntityType]) -> QueryCondition:
        def inner() -> sa.sql.expression.ColumnElement[bool]:
            return VirtualEntityRow.entity_type.not_in(list(scope_types))

        return inner

    @staticmethod
    def by_scope_id(scope_id: EntityID) -> QueryCondition:
        def inner() -> sa.sql.expression.ColumnElement[bool]:
            return VirtualEntityRow.entity_id == scope_id

        return inner

    @staticmethod
    def by_scope_id_contains(spec: StringMatchSpec) -> QueryCondition:
        def inner() -> sa.sql.expression.ColumnElement[bool]:
            if spec.case_insensitive:
                condition = _scope_id_text().ilike(f"%{spec.value}%")
            else:
                condition = _scope_id_text().like(f"%{spec.value}%")
            if spec.negated:
                condition = sa.not_(condition)
            return condition

        return inner

    @staticmethod
    def by_scope_id_equals(spec: StringMatchSpec) -> QueryCondition:
        def inner() -> sa.sql.expression.ColumnElement[bool]:
            if spec.case_insensitive:
                condition = sa.func.lower(_scope_id_text()) == spec.value.lower()
            else:
                condition = _scope_id_text() == spec.value
            if spec.negated:
                condition = sa.not_(condition)
            return condition

        return inner

    @staticmethod
    def by_scope_id_starts_with(spec: StringMatchSpec) -> QueryCondition:
        def inner() -> sa.sql.expression.ColumnElement[bool]:
            if spec.case_insensitive:
                condition = _scope_id_text().ilike(f"{spec.value}%")
            else:
                condition = _scope_id_text().like(f"{spec.value}%")
            if spec.negated:
                condition = sa.not_(condition)
            return condition

        return inner

    @staticmethod
    def by_scope_id_ends_with(spec: StringMatchSpec) -> QueryCondition:
        def inner() -> sa.sql.expression.ColumnElement[bool]:
            if spec.case_insensitive:
                condition = _scope_id_text().ilike(f"%{spec.value}")
            else:
                condition = _scope_id_text().like(f"%{spec.value}")
            if spec.negated:
                condition = sa.not_(condition)
            return condition

        return inner

    @staticmethod
    def by_scope_id_in(spec: StringInMatchSpec) -> QueryCondition:
        def inner() -> sa.sql.expression.ColumnElement[bool]:
            if spec.case_insensitive:
                condition = sa.func.lower(_scope_id_text()).in_([
                    value.lower() for value in spec.values
                ])
            else:
                condition = _scope_id_text().in_(spec.values)
            if spec.negated:
                condition = sa.not_(condition)
            return condition

        return inner
