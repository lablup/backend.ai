"""Query conditions for model card rows."""

from __future__ import annotations

from uuid import UUID

import sqlalchemy as sa

from ai.backend.common.data.filter_specs import StringMatchSpec
from ai.backend.manager.models.condition_utils import (
    make_nested_string_in_factory,
    make_string_in_factory,
)
from ai.backend.manager.models.model_card.row import ModelCardRow
from ai.backend.manager.models.vfolder.row import VFolderRow
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

    by_name_in = staticmethod(make_string_in_factory(ModelCardRow.name))

    # ==================== Storage Host Nested Filters ====================

    @staticmethod
    def _exists_vfolder(
        *vfolder_conditions: sa.sql.expression.ColumnElement[bool],
    ) -> sa.sql.expression.ColumnElement[bool]:
        """EXISTS subquery: ModelCard -> VFolder (via FK ``ModelCardRow.vfolder``)."""
        subq = sa.select(sa.literal(1)).where(VFolderRow.id == ModelCardRow.vfolder)
        for cond in vfolder_conditions:
            subq = subq.where(cond)
        return sa.exists(subq)

    @staticmethod
    def by_storage_host_equals(spec: StringMatchSpec) -> QueryCondition:
        def inner() -> sa.sql.expression.ColumnElement[bool]:
            if spec.case_insensitive:
                cond = sa.func.lower(VFolderRow.host) == spec.value.lower()
            else:
                cond = VFolderRow.host == spec.value
            if spec.negated:
                cond = sa.not_(cond)
            return ModelCardConditions._exists_vfolder(cond)

        return inner

    @staticmethod
    def by_storage_host_contains(spec: StringMatchSpec) -> QueryCondition:
        def inner() -> sa.sql.expression.ColumnElement[bool]:
            if spec.case_insensitive:
                cond = VFolderRow.host.ilike(f"%{spec.value}%")
            else:
                cond = VFolderRow.host.like(f"%{spec.value}%")
            if spec.negated:
                cond = sa.not_(cond)
            return ModelCardConditions._exists_vfolder(cond)

        return inner

    @staticmethod
    def by_storage_host_starts_with(spec: StringMatchSpec) -> QueryCondition:
        def inner() -> sa.sql.expression.ColumnElement[bool]:
            if spec.case_insensitive:
                cond = VFolderRow.host.ilike(f"{spec.value}%")
            else:
                cond = VFolderRow.host.like(f"{spec.value}%")
            if spec.negated:
                cond = sa.not_(cond)
            return ModelCardConditions._exists_vfolder(cond)

        return inner

    @staticmethod
    def by_storage_host_ends_with(spec: StringMatchSpec) -> QueryCondition:
        def inner() -> sa.sql.expression.ColumnElement[bool]:
            if spec.case_insensitive:
                cond = VFolderRow.host.ilike(f"%{spec.value}")
            else:
                cond = VFolderRow.host.like(f"%{spec.value}")
            if spec.negated:
                cond = sa.not_(cond)
            return ModelCardConditions._exists_vfolder(cond)

        return inner

    by_storage_host_in = staticmethod(
        make_nested_string_in_factory(
            VFolderRow.host,
            lambda c: ModelCardConditions._exists_vfolder(c),
        )
    )

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
