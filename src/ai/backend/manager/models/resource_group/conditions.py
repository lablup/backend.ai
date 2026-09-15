"""Query conditions for scaling group rows."""

from __future__ import annotations

import uuid
from collections.abc import Collection

import sqlalchemy as sa

from ai.backend.common.data.entity.resource_group import ResourceGroupID
from ai.backend.common.data.filter_specs import StringMatchSpec
from ai.backend.manager.models.clauses import QueryCondition
from ai.backend.manager.models.condition_utils import make_string_in_factory
from ai.backend.manager.models.resource_group import (
    ResourceGroupForProjectRow,
    ResourceGroupRow,
)

__all__ = ("ResourceGroupConditions",)


class ResourceGroupConditions:
    """Query conditions for scaling groups."""

    @staticmethod
    def by_ids(ids: Collection[ResourceGroupID]) -> QueryCondition:
        def inner() -> sa.sql.expression.ColumnElement[bool]:
            return ResourceGroupRow.id.in_(ids)

        return inner

    @staticmethod
    def by_name_contains(spec: StringMatchSpec) -> QueryCondition:
        def inner() -> sa.sql.expression.ColumnElement[bool]:
            if spec.case_insensitive:
                condition = ResourceGroupRow.name.ilike(f"%{spec.value}%")
            else:
                condition = ResourceGroupRow.name.like(f"%{spec.value}%")
            if spec.negated:
                condition = sa.not_(condition)
            return condition

        return inner

    @staticmethod
    def by_name_equals(spec: StringMatchSpec) -> QueryCondition:
        def inner() -> sa.sql.expression.ColumnElement[bool]:
            if spec.case_insensitive:
                condition = sa.func.lower(ResourceGroupRow.name) == spec.value.lower()
            else:
                condition = ResourceGroupRow.name == spec.value
            if spec.negated:
                condition = sa.not_(condition)
            return condition

        return inner

    @staticmethod
    def by_name_starts_with(spec: StringMatchSpec) -> QueryCondition:
        def inner() -> sa.sql.expression.ColumnElement[bool]:
            if spec.case_insensitive:
                condition = ResourceGroupRow.name.ilike(f"{spec.value}%")
            else:
                condition = ResourceGroupRow.name.like(f"{spec.value}%")
            if spec.negated:
                condition = sa.not_(condition)
            return condition

        return inner

    @staticmethod
    def by_name_ends_with(spec: StringMatchSpec) -> QueryCondition:
        def inner() -> sa.sql.expression.ColumnElement[bool]:
            if spec.case_insensitive:
                condition = ResourceGroupRow.name.ilike(f"%{spec.value}")
            else:
                condition = ResourceGroupRow.name.like(f"%{spec.value}")
            if spec.negated:
                condition = sa.not_(condition)
            return condition

        return inner

    @staticmethod
    def by_description_contains(spec: StringMatchSpec) -> QueryCondition:
        def inner() -> sa.sql.expression.ColumnElement[bool]:
            if spec.case_insensitive:
                condition = ResourceGroupRow.description.ilike(f"%{spec.value}%")
            else:
                condition = ResourceGroupRow.description.like(f"%{spec.value}%")
            if spec.negated:
                condition = sa.not_(condition)
            return condition

        return inner

    @staticmethod
    def by_description_equals(spec: StringMatchSpec) -> QueryCondition:
        def inner() -> sa.sql.expression.ColumnElement[bool]:
            if spec.case_insensitive:
                condition = sa.func.lower(ResourceGroupRow.description) == spec.value.lower()
            else:
                condition = ResourceGroupRow.description == spec.value
            if spec.negated:
                condition = sa.not_(condition)
            return condition

        return inner

    @staticmethod
    def by_description_starts_with(spec: StringMatchSpec) -> QueryCondition:
        def inner() -> sa.sql.expression.ColumnElement[bool]:
            if spec.case_insensitive:
                condition = ResourceGroupRow.description.ilike(f"{spec.value}%")
            else:
                condition = ResourceGroupRow.description.like(f"{spec.value}%")
            if spec.negated:
                condition = sa.not_(condition)
            return condition

        return inner

    @staticmethod
    def by_description_ends_with(spec: StringMatchSpec) -> QueryCondition:
        def inner() -> sa.sql.expression.ColumnElement[bool]:
            if spec.case_insensitive:
                condition = ResourceGroupRow.description.ilike(f"%{spec.value}")
            else:
                condition = ResourceGroupRow.description.like(f"%{spec.value}")
            if spec.negated:
                condition = sa.not_(condition)
            return condition

        return inner

    by_name_in = staticmethod(make_string_in_factory(ResourceGroupRow.name))
    by_description_in = staticmethod(make_string_in_factory(ResourceGroupRow.description))

    @staticmethod
    def by_is_active(is_active: bool) -> QueryCondition:
        def inner() -> sa.sql.expression.ColumnElement[bool]:
            return ResourceGroupRow.is_active == is_active

        return inner

    @staticmethod
    def by_is_public(is_public: bool) -> QueryCondition:
        def inner() -> sa.sql.expression.ColumnElement[bool]:
            return ResourceGroupRow.is_public == is_public

        return inner

    @staticmethod
    def by_is_default(is_default: bool) -> QueryCondition:
        def inner() -> sa.sql.expression.ColumnElement[bool]:
            return ResourceGroupRow.is_default == is_default

        return inner

    @staticmethod
    def by_scheduler(scheduler: str) -> QueryCondition:
        def inner() -> sa.sql.expression.ColumnElement[bool]:
            return ResourceGroupRow.scheduler == scheduler

        return inner

    @staticmethod
    def by_use_host_network(use_host_network: bool) -> QueryCondition:
        def inner() -> sa.sql.expression.ColumnElement[bool]:
            return ResourceGroupRow.use_host_network == use_host_network

        return inner

    @staticmethod
    def by_names(names: Collection[str]) -> QueryCondition:
        def inner() -> sa.sql.expression.ColumnElement[bool]:
            return ResourceGroupRow.name.in_(names)

        return inner

    @staticmethod
    def by_project(project_id: str) -> QueryCondition:
        def inner() -> sa.sql.expression.ColumnElement[bool]:
            return ResourceGroupRow.id.in_(
                sa.select(ResourceGroupForProjectRow.resource_group_id).where(
                    ResourceGroupForProjectRow.group == project_id
                )
            )

        return inner

    @staticmethod
    def by_cursor_forward(cursor_id: str) -> QueryCondition:
        """Cursor condition for forward pagination (after cursor).

        The cursor value is the resource group UUID; a subquery fetches the
        cursor row's created_at to compare against.
        """
        rg_id = ResourceGroupID(uuid.UUID(cursor_id))

        def inner() -> sa.sql.expression.ColumnElement[bool]:
            subquery = (
                sa.select(ResourceGroupRow.created_at)
                .where(ResourceGroupRow.id == rg_id)
                .scalar_subquery()
            )
            return ResourceGroupRow.created_at < subquery

        return inner

    @staticmethod
    def by_cursor_backward(cursor_id: str) -> QueryCondition:
        """Cursor condition for backward pagination (before cursor).

        The cursor value is the resource group UUID; a subquery fetches the
        cursor row's created_at to compare against.
        """
        rg_id = ResourceGroupID(uuid.UUID(cursor_id))

        def inner() -> sa.sql.expression.ColumnElement[bool]:
            subquery = (
                sa.select(ResourceGroupRow.created_at)
                .where(ResourceGroupRow.id == rg_id)
                .scalar_subquery()
            )
            return ResourceGroupRow.created_at > subquery

        return inner
