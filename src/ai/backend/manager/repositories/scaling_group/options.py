from __future__ import annotations

from collections.abc import Collection

import sqlalchemy as sa

from ai.backend.manager.api.gql.base import StringMatchSpec
from ai.backend.manager.models.scaling_group import (
    ScalingGroupForProjectRow,
    ScalingGroupRow,
)
from ai.backend.manager.repositories.base import QueryCondition, QueryOrder


class ScalingGroupConditions:
    """Query conditions for scaling groups."""

    @staticmethod
    def by_name_contains(spec: StringMatchSpec) -> QueryCondition:
        def inner() -> sa.sql.expression.ColumnElement[bool]:
            if spec.case_insensitive:
                condition = ScalingGroupRow.name.ilike(f"%{spec.value}%")
            else:
                condition = ScalingGroupRow.name.like(f"%{spec.value}%")
            if spec.negated:
                condition = sa.not_(condition)
            return condition

        return inner

    @staticmethod
    def by_name_equals(spec: StringMatchSpec) -> QueryCondition:
        def inner() -> sa.sql.expression.ColumnElement[bool]:
            if spec.case_insensitive:
                condition = sa.func.lower(ScalingGroupRow.name) == spec.value.lower()
            else:
                condition = ScalingGroupRow.name == spec.value
            if spec.negated:
                condition = sa.not_(condition)
            return condition

        return inner

    @staticmethod
    def by_name_starts_with(spec: StringMatchSpec) -> QueryCondition:
        def inner() -> sa.sql.expression.ColumnElement[bool]:
            if spec.case_insensitive:
                condition = ScalingGroupRow.name.ilike(f"{spec.value}%")
            else:
                condition = ScalingGroupRow.name.like(f"{spec.value}%")
            if spec.negated:
                condition = sa.not_(condition)
            return condition

        return inner

    @staticmethod
    def by_name_ends_with(spec: StringMatchSpec) -> QueryCondition:
        def inner() -> sa.sql.expression.ColumnElement[bool]:
            if spec.case_insensitive:
                condition = ScalingGroupRow.name.ilike(f"%{spec.value}")
            else:
                condition = ScalingGroupRow.name.like(f"%{spec.value}")
            if spec.negated:
                condition = sa.not_(condition)
            return condition

        return inner

    @staticmethod
    def by_description_contains(spec: StringMatchSpec) -> QueryCondition:
        def inner() -> sa.sql.expression.ColumnElement[bool]:
            if spec.case_insensitive:
                condition = ScalingGroupRow.description.ilike(f"%{spec.value}%")
            else:
                condition = ScalingGroupRow.description.like(f"%{spec.value}%")
            if spec.negated:
                condition = sa.not_(condition)
            return condition

        return inner

    @staticmethod
    def by_description_equals(spec: StringMatchSpec) -> QueryCondition:
        def inner() -> sa.sql.expression.ColumnElement[bool]:
            if spec.case_insensitive:
                condition = sa.func.lower(ScalingGroupRow.description) == spec.value.lower()
            else:
                condition = ScalingGroupRow.description == spec.value
            if spec.negated:
                condition = sa.not_(condition)
            return condition

        return inner

    @staticmethod
    def by_description_starts_with(spec: StringMatchSpec) -> QueryCondition:
        def inner() -> sa.sql.expression.ColumnElement[bool]:
            if spec.case_insensitive:
                condition = ScalingGroupRow.description.ilike(f"{spec.value}%")
            else:
                condition = ScalingGroupRow.description.like(f"{spec.value}%")
            if spec.negated:
                condition = sa.not_(condition)
            return condition

        return inner

    @staticmethod
    def by_description_ends_with(spec: StringMatchSpec) -> QueryCondition:
        def inner() -> sa.sql.expression.ColumnElement[bool]:
            if spec.case_insensitive:
                condition = ScalingGroupRow.description.ilike(f"%{spec.value}")
            else:
                condition = ScalingGroupRow.description.like(f"%{spec.value}")
            if spec.negated:
                condition = sa.not_(condition)
            return condition

        return inner

    @staticmethod
    def by_is_active(is_active: bool) -> QueryCondition:
        def inner() -> sa.sql.expression.ColumnElement[bool]:
            return ScalingGroupRow.is_active == is_active

        return inner

    @staticmethod
    def by_is_public(is_public: bool) -> QueryCondition:
        def inner() -> sa.sql.expression.ColumnElement[bool]:
            return ScalingGroupRow.is_public == is_public

        return inner

    @staticmethod
    def by_scheduler(scheduler: str) -> QueryCondition:
        def inner() -> sa.sql.expression.ColumnElement[bool]:
            return ScalingGroupRow.scheduler == scheduler

        return inner

    @staticmethod
    def by_use_host_network(use_host_network: bool) -> QueryCondition:
        def inner() -> sa.sql.expression.ColumnElement[bool]:
            return ScalingGroupRow.use_host_network == use_host_network

        return inner

    @staticmethod
    def by_names(names: Collection[str]) -> QueryCondition:
        def inner() -> sa.sql.expression.ColumnElement[bool]:
            return ScalingGroupRow.name.in_(names)

        return inner

    @staticmethod
    def by_project(project_id: str) -> QueryCondition:
        def inner() -> sa.sql.expression.ColumnElement[bool]:
            return ScalingGroupRow.name.in_(
                sa.select(ScalingGroupForProjectRow.scaling_group).where(
                    ScalingGroupForProjectRow.group == project_id
                )
            )

        return inner

    @staticmethod
    def by_cursor_forward(cursor_name: str) -> QueryCondition:
        """Cursor condition for forward pagination (after cursor).

        Uses subquery to get created_at of the cursor row and compare.
        ScalingGroup uses name as primary key.
        """

        def inner() -> sa.sql.expression.ColumnElement[bool]:
            subquery = (
                sa.select(ScalingGroupRow.created_at)
                .where(ScalingGroupRow.name == cursor_name)
                .scalar_subquery()
            )
            return ScalingGroupRow.created_at < subquery

        return inner

    @staticmethod
    def by_cursor_backward(cursor_name: str) -> QueryCondition:
        """Cursor condition for backward pagination (before cursor).

        Uses subquery to get created_at of the cursor row and compare.
        ScalingGroup uses name as primary key.
        """

        def inner() -> sa.sql.expression.ColumnElement[bool]:
            subquery = (
                sa.select(ScalingGroupRow.created_at)
                .where(ScalingGroupRow.name == cursor_name)
                .scalar_subquery()
            )
            return ScalingGroupRow.created_at > subquery

        return inner


class ScalingGroupOrders:
    """Query orders for scaling groups."""

    @staticmethod
    def name(ascending: bool = True) -> QueryOrder:
        if ascending:
            return ScalingGroupRow.name.asc()
        return ScalingGroupRow.name.desc()

    @staticmethod
    def created_at(ascending: bool = True) -> QueryOrder:
        if ascending:
            return ScalingGroupRow.created_at.asc()
        return ScalingGroupRow.created_at.desc()

    @staticmethod
    def is_active(ascending: bool = True) -> QueryOrder:
        if ascending:
            return ScalingGroupRow.is_active.asc()
        return ScalingGroupRow.is_active.desc()

    @staticmethod
    def is_public(ascending: bool = True) -> QueryOrder:
        if ascending:
            return ScalingGroupRow.is_public.asc()
        return ScalingGroupRow.is_public.desc()
