"""Query conditions for deployment revision preset rows."""

from __future__ import annotations

import uuid
from uuid import UUID

import sqlalchemy as sa

from ai.backend.common.data.filter_specs import (
    StringMatchSpec,
    UUIDEqualMatchSpec,
    UUIDInMatchSpec,
)
from ai.backend.manager.models.clauses import QueryCondition
from ai.backend.manager.models.condition_utils import make_string_in_factory
from ai.backend.manager.models.deployment_revision_preset.row import DeploymentRevisionPresetRow

__all__ = ("DeploymentRevisionPresetConditions",)


class DeploymentRevisionPresetConditions:
    @staticmethod
    def by_runtime_variant_id(variant_id: UUID) -> QueryCondition:
        def inner() -> sa.sql.expression.ColumnElement[bool]:
            return DeploymentRevisionPresetRow.runtime_variant == variant_id

        return inner

    @staticmethod
    def by_runtime_variant_id_equals(spec: UUIDEqualMatchSpec) -> QueryCondition:
        def inner() -> sa.sql.expression.ColumnElement[bool]:
            condition = DeploymentRevisionPresetRow.runtime_variant == spec.value
            if spec.negated:
                condition = sa.not_(condition)
            return condition

        return inner

    @staticmethod
    def by_runtime_variant_id_in(spec: UUIDInMatchSpec) -> QueryCondition:
        def inner() -> sa.sql.expression.ColumnElement[bool]:
            condition = DeploymentRevisionPresetRow.runtime_variant.in_(spec.values)
            if spec.negated:
                condition = sa.not_(condition)
            return condition

        return inner

    @staticmethod
    def by_name_contains(spec: StringMatchSpec) -> QueryCondition:
        def inner() -> sa.sql.expression.ColumnElement[bool]:
            if spec.case_insensitive:
                condition = DeploymentRevisionPresetRow.name.ilike(f"%{spec.value}%")
            else:
                condition = DeploymentRevisionPresetRow.name.like(f"%{spec.value}%")
            if spec.negated:
                condition = sa.not_(condition)
            return condition

        return inner

    @staticmethod
    def by_name_equals(spec: StringMatchSpec) -> QueryCondition:
        def inner() -> sa.sql.expression.ColumnElement[bool]:
            if spec.case_insensitive:
                condition = sa.func.lower(DeploymentRevisionPresetRow.name) == spec.value.lower()
            else:
                condition = DeploymentRevisionPresetRow.name == spec.value
            if spec.negated:
                condition = sa.not_(condition)
            return condition

        return inner

    @staticmethod
    def by_name_starts_with(spec: StringMatchSpec) -> QueryCondition:
        def inner() -> sa.sql.expression.ColumnElement[bool]:
            if spec.case_insensitive:
                condition = DeploymentRevisionPresetRow.name.ilike(f"{spec.value}%")
            else:
                condition = DeploymentRevisionPresetRow.name.like(f"{spec.value}%")
            if spec.negated:
                condition = sa.not_(condition)
            return condition

        return inner

    @staticmethod
    def by_name_ends_with(spec: StringMatchSpec) -> QueryCondition:
        def inner() -> sa.sql.expression.ColumnElement[bool]:
            if spec.case_insensitive:
                condition = DeploymentRevisionPresetRow.name.ilike(f"%{spec.value}")
            else:
                condition = DeploymentRevisionPresetRow.name.like(f"%{spec.value}")
            if spec.negated:
                condition = sa.not_(condition)
            return condition

        return inner

    by_name_in = staticmethod(make_string_in_factory(DeploymentRevisionPresetRow.name))

    @staticmethod
    def by_id_equals(spec: UUIDEqualMatchSpec) -> QueryCondition:
        def inner() -> sa.sql.expression.ColumnElement[bool]:
            condition = DeploymentRevisionPresetRow.id == spec.value
            if spec.negated:
                condition = sa.not_(condition)
            return condition

        return inner

    @staticmethod
    def by_id_in(spec: UUIDInMatchSpec) -> QueryCondition:
        def inner() -> sa.sql.expression.ColumnElement[bool]:
            condition = DeploymentRevisionPresetRow.id.in_(spec.values)
            if spec.negated:
                condition = sa.not_(condition)
            return condition

        return inner

    @staticmethod
    def by_cursor_forward(cursor_id: str) -> QueryCondition:
        """Cursor condition for forward pagination (after cursor).

        Reads the cursor row's ``created_at`` and compares against that, because that is what
        the page is ordered by — comparing ids would draw the page boundary on a column the
        result is not sorted by.
        """
        cursor_uuid = uuid.UUID(cursor_id)

        def inner() -> sa.sql.expression.ColumnElement[bool]:
            subquery = (
                sa.select(DeploymentRevisionPresetRow.created_at)
                .where(DeploymentRevisionPresetRow.id == cursor_uuid)
                .scalar_subquery()
            )
            return DeploymentRevisionPresetRow.created_at < subquery

        return inner

    @staticmethod
    def by_cursor_backward(cursor_id: str) -> QueryCondition:
        """Cursor condition for backward pagination (before cursor).

        Reads the cursor row's ``created_at`` and compares against that, because that is what
        the page is ordered by — comparing ids would draw the page boundary on a column the
        result is not sorted by.
        """
        cursor_uuid = uuid.UUID(cursor_id)

        def inner() -> sa.sql.expression.ColumnElement[bool]:
            subquery = (
                sa.select(DeploymentRevisionPresetRow.created_at)
                .where(DeploymentRevisionPresetRow.id == cursor_uuid)
                .scalar_subquery()
            )
            return DeploymentRevisionPresetRow.created_at > subquery

        return inner
