"""Query conditions for model card rows."""

from __future__ import annotations

from uuid import UUID

import sqlalchemy as sa

from ai.backend.common.data.filter_specs import StringMatchSpec
from ai.backend.manager.models.model_card.row import ModelCardRow
from ai.backend.manager.repositories.base import QueryCondition

__all__ = ("ModelCardConditions",)


class ModelCardConditions:
    @staticmethod
    def by_domain(domain_name: str) -> QueryCondition:
        def inner() -> sa.sql.expression.ColumnElement[bool]:
            return ModelCardRow.domain == domain_name

        return inner

    @staticmethod
    def by_project(project_id: UUID) -> QueryCondition:
        def inner() -> sa.sql.expression.ColumnElement[bool]:
            return ModelCardRow.project == project_id

        return inner

    @staticmethod
    def by_creator(creator_id: UUID) -> QueryCondition:
        def inner() -> sa.sql.expression.ColumnElement[bool]:
            return ModelCardRow.creator == creator_id

        return inner

    @staticmethod
    def by_name_contains(spec: StringMatchSpec) -> QueryCondition:
        def inner() -> sa.sql.expression.ColumnElement[bool]:
            if spec.case_insensitive:
                condition = ModelCardRow.name.ilike(f"%{spec.value}%")
            else:
                condition = ModelCardRow.name.like(f"%{spec.value}%")
            if spec.negated:
                condition = sa.not_(condition)
            return condition

        return inner

    @staticmethod
    def by_name_equals(spec: StringMatchSpec) -> QueryCondition:
        def inner() -> sa.sql.expression.ColumnElement[bool]:
            if spec.case_insensitive:
                condition = sa.func.lower(ModelCardRow.name) == spec.value.lower()
            else:
                condition = ModelCardRow.name == spec.value
            if spec.negated:
                condition = sa.not_(condition)
            return condition

        return inner

    @staticmethod
    def by_name_starts_with(spec: StringMatchSpec) -> QueryCondition:
        def inner() -> sa.sql.expression.ColumnElement[bool]:
            if spec.case_insensitive:
                condition = ModelCardRow.name.ilike(f"{spec.value}%")
            else:
                condition = ModelCardRow.name.like(f"{spec.value}%")
            if spec.negated:
                condition = sa.not_(condition)
            return condition

        return inner

    @staticmethod
    def by_name_ends_with(spec: StringMatchSpec) -> QueryCondition:
        def inner() -> sa.sql.expression.ColumnElement[bool]:
            if spec.case_insensitive:
                condition = ModelCardRow.name.ilike(f"%{spec.value}")
            else:
                condition = ModelCardRow.name.like(f"%{spec.value}")
            if spec.negated:
                condition = sa.not_(condition)
            return condition

        return inner

    @staticmethod
    def by_cursor_forward(cursor_id: str) -> QueryCondition:
        def inner() -> sa.sql.expression.ColumnElement[bool]:
            return ModelCardRow.id < sa.text(f"'{cursor_id}'::uuid")

        return inner

    @staticmethod
    def by_cursor_backward(cursor_id: str) -> QueryCondition:
        def inner() -> sa.sql.expression.ColumnElement[bool]:
            return ModelCardRow.id > sa.text(f"'{cursor_id}'::uuid")

        return inner
