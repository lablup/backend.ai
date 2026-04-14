"""Query conditions for the prometheus_query_preset_category domain."""

from __future__ import annotations

from collections.abc import Collection

import sqlalchemy as sa

from ai.backend.common.data.filter_specs import StringMatchSpec
from ai.backend.manager.models.condition_utils import make_string_in_factory
from ai.backend.manager.models.prometheus_query_preset_category import (
    PrometheusQueryPresetCategoryRow,
)
from ai.backend.manager.repositories.base import QueryCondition


class PrometheusQueryPresetCategoryConditions:
    """QueryCondition factories for prometheus query preset category filtering."""

    @staticmethod
    def by_ids(category_ids: Collection[str]) -> QueryCondition:
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
