"""Query conditions for the prometheus_query_preset_category domain."""

from __future__ import annotations

import uuid
from collections.abc import Collection

import sqlalchemy as sa

from ai.backend.common.data.filter_specs import StringMatchSpec
from ai.backend.manager.models.clauses import QueryCondition
from ai.backend.manager.models.condition_utils import make_string_in_factory
from ai.backend.manager.models.prometheus_query_preset_category import (
    PrometheusQueryPresetCategoryRow,
)


class PrometheusQueryPresetCategoryConditions:
    """QueryCondition factories for prometheus query preset category filtering."""

    @staticmethod
    def by_ids(category_ids: Collection[uuid.UUID]) -> QueryCondition:
        def inner() -> sa.ColumnElement[bool]:
            return PrometheusQueryPresetCategoryRow.id.in_(category_ids)

        return inner

    @staticmethod
    def by_name_contains(spec: StringMatchSpec) -> QueryCondition:
        def inner() -> sa.ColumnElement[bool]:
            if spec.case_insensitive:
                condition = PrometheusQueryPresetCategoryRow.name.ilike(f"%{spec.value}%")
            else:
                condition = PrometheusQueryPresetCategoryRow.name.like(f"%{spec.value}%")
            if spec.negated:
                condition = sa.not_(condition)
            return condition

        return inner

    @staticmethod
    def by_name_equals(spec: StringMatchSpec) -> QueryCondition:
        def inner() -> sa.ColumnElement[bool]:
            if spec.case_insensitive:
                condition = (
                    sa.func.lower(PrometheusQueryPresetCategoryRow.name) == spec.value.lower()
                )
            else:
                condition = PrometheusQueryPresetCategoryRow.name == spec.value
            if spec.negated:
                condition = sa.not_(condition)
            return condition

        return inner

    @staticmethod
    def by_name_starts_with(spec: StringMatchSpec) -> QueryCondition:
        def inner() -> sa.ColumnElement[bool]:
            if spec.case_insensitive:
                condition = PrometheusQueryPresetCategoryRow.name.ilike(f"{spec.value}%")
            else:
                condition = PrometheusQueryPresetCategoryRow.name.like(f"{spec.value}%")
            if spec.negated:
                condition = sa.not_(condition)
            return condition

        return inner

    @staticmethod
    def by_name_ends_with(spec: StringMatchSpec) -> QueryCondition:
        def inner() -> sa.ColumnElement[bool]:
            if spec.case_insensitive:
                condition = PrometheusQueryPresetCategoryRow.name.ilike(f"%{spec.value}")
            else:
                condition = PrometheusQueryPresetCategoryRow.name.like(f"%{spec.value}")
            if spec.negated:
                condition = sa.not_(condition)
            return condition

        return inner

    by_name_in = staticmethod(make_string_in_factory(PrometheusQueryPresetCategoryRow.name))

    @staticmethod
    def by_cursor_forward(cursor_id: str) -> QueryCondition:
        cursor_uuid = uuid.UUID(cursor_id)

        def inner() -> sa.ColumnElement[bool]:
            subquery = (
                sa.select(PrometheusQueryPresetCategoryRow.created_at)
                .where(PrometheusQueryPresetCategoryRow.id == cursor_uuid)
                .scalar_subquery()
            )
            return PrometheusQueryPresetCategoryRow.created_at < subquery

        return inner

    @staticmethod
    def by_cursor_backward(cursor_id: str) -> QueryCondition:
        cursor_uuid = uuid.UUID(cursor_id)

        def inner() -> sa.ColumnElement[bool]:
            subquery = (
                sa.select(PrometheusQueryPresetCategoryRow.created_at)
                .where(PrometheusQueryPresetCategoryRow.id == cursor_uuid)
                .scalar_subquery()
            )
            return PrometheusQueryPresetCategoryRow.created_at > subquery

        return inner
