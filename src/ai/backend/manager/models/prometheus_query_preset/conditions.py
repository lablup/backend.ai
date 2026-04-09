"""Query conditions for the prometheus_query_preset domain."""

from __future__ import annotations

import uuid
from collections.abc import Collection

import sqlalchemy as sa

from ai.backend.common.data.filter_specs import StringMatchSpec
from ai.backend.manager.models.condition_utils import make_string_in_factory
from ai.backend.manager.models.prometheus_query_preset import PrometheusQueryPresetRow
from ai.backend.manager.repositories.base import QueryCondition


class PrometheusQueryPresetConditions:
    """QueryCondition factories for prometheus query preset filtering."""

    @staticmethod
    def by_ids(preset_ids: Collection[uuid.UUID]) -> QueryCondition:
        def inner() -> sa.ColumnElement[bool]:
            return PrometheusQueryPresetRow.id.in_(preset_ids)

        return inner

    @staticmethod
    def by_name_contains(spec: StringMatchSpec) -> QueryCondition:
        def inner() -> sa.ColumnElement[bool]:
            if spec.case_insensitive:
                condition = PrometheusQueryPresetRow.name.ilike(f"%{spec.value}%")
            else:
                condition = PrometheusQueryPresetRow.name.like(f"%{spec.value}%")
            if spec.negated:
                condition = sa.not_(condition)
            return condition

        return inner

    @staticmethod
    def by_name_equals(spec: StringMatchSpec) -> QueryCondition:
        def inner() -> sa.ColumnElement[bool]:
            if spec.case_insensitive:
                condition = sa.func.lower(PrometheusQueryPresetRow.name) == spec.value.lower()
            else:
                condition = PrometheusQueryPresetRow.name == spec.value
            if spec.negated:
                condition = sa.not_(condition)
            return condition

        return inner

    @staticmethod
    def by_name_starts_with(spec: StringMatchSpec) -> QueryCondition:
        def inner() -> sa.ColumnElement[bool]:
            if spec.case_insensitive:
                condition = PrometheusQueryPresetRow.name.ilike(f"{spec.value}%")
            else:
                condition = PrometheusQueryPresetRow.name.like(f"{spec.value}%")
            if spec.negated:
                condition = sa.not_(condition)
            return condition

        return inner

    @staticmethod
    def by_name_ends_with(spec: StringMatchSpec) -> QueryCondition:
        def inner() -> sa.ColumnElement[bool]:
            if spec.case_insensitive:
                condition = PrometheusQueryPresetRow.name.ilike(f"%{spec.value}")
            else:
                condition = PrometheusQueryPresetRow.name.like(f"%{spec.value}")
            if spec.negated:
                condition = sa.not_(condition)
            return condition

        return inner

    by_name_in = staticmethod(make_string_in_factory(PrometheusQueryPresetRow.name))

    @staticmethod
    def by_metric_name_equals(metric_name: str) -> QueryCondition:
        def inner() -> sa.ColumnElement[bool]:
            return PrometheusQueryPresetRow.metric_name == metric_name

        return inner

    @staticmethod
    def by_cursor_forward(cursor_id: str) -> QueryCondition:
        cursor_uuid = uuid.UUID(cursor_id)

        def inner() -> sa.ColumnElement[bool]:
            subquery = (
                sa.select(PrometheusQueryPresetRow.created_at)
                .where(PrometheusQueryPresetRow.id == cursor_uuid)
                .scalar_subquery()
            )
            return PrometheusQueryPresetRow.created_at < subquery

        return inner

    @staticmethod
    def by_cursor_backward(cursor_id: str) -> QueryCondition:
        cursor_uuid = uuid.UUID(cursor_id)

        def inner() -> sa.ColumnElement[bool]:
            subquery = (
                sa.select(PrometheusQueryPresetRow.created_at)
                .where(PrometheusQueryPresetRow.id == cursor_uuid)
                .scalar_subquery()
            )
            return PrometheusQueryPresetRow.created_at > subquery

        return inner
