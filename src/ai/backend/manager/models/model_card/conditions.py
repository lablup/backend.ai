"""Query conditions for model card rows."""

from __future__ import annotations

import uuid
from collections.abc import Collection
from uuid import UUID

import sqlalchemy as sa

from ai.backend.common.data.filter_specs import (
    StringMatchSpec,
    UUIDEqualMatchSpec,
    UUIDInMatchSpec,
)
from ai.backend.common.identifier.vfolder import VFolderUUID
from ai.backend.manager.models.clauses import QueryCondition
from ai.backend.manager.models.condition_utils import (
    make_nested_string_in_factory,
    make_string_in_factory,
)
from ai.backend.manager.models.model_card.row import ModelCardRow
from ai.backend.manager.models.vfolder.row import VFolderRow

__all__ = ("ModelCardConditions",)


class ModelCardConditions:
    @staticmethod
    def by_vfolder_ids(vfolder_ids: Collection[VFolderUUID]) -> QueryCondition:
        def inner() -> sa.sql.expression.ColumnElement[bool]:
            return ModelCardRow.vfolder.in_(vfolder_ids)

        return inner

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
    def by_project_equals(spec: UUIDEqualMatchSpec) -> QueryCondition:
        def inner() -> sa.sql.expression.ColumnElement[bool]:
            condition = ModelCardRow.project == spec.value
            if spec.negated:
                condition = sa.not_(condition)
            return condition

        return inner

    @staticmethod
    def by_project_in(spec: UUIDInMatchSpec) -> QueryCondition:
        def inner() -> sa.sql.expression.ColumnElement[bool]:
            condition = ModelCardRow.project.in_(spec.values)
            if spec.negated:
                condition = sa.not_(condition)
            return condition

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

    @staticmethod
    def by_domain_contains(spec: StringMatchSpec) -> QueryCondition:
        def inner() -> sa.sql.expression.ColumnElement[bool]:
            if spec.case_insensitive:
                condition = ModelCardRow.domain.ilike(f"%{spec.value}%")
            else:
                condition = ModelCardRow.domain.like(f"%{spec.value}%")
            if spec.negated:
                condition = sa.not_(condition)
            return condition

        return inner

    @staticmethod
    def by_domain_equals(spec: StringMatchSpec) -> QueryCondition:
        def inner() -> sa.sql.expression.ColumnElement[bool]:
            if spec.case_insensitive:
                condition = sa.func.lower(ModelCardRow.domain) == spec.value.lower()
            else:
                condition = ModelCardRow.domain == spec.value
            if spec.negated:
                condition = sa.not_(condition)
            return condition

        return inner

    @staticmethod
    def by_domain_starts_with(spec: StringMatchSpec) -> QueryCondition:
        def inner() -> sa.sql.expression.ColumnElement[bool]:
            if spec.case_insensitive:
                condition = ModelCardRow.domain.ilike(f"{spec.value}%")
            else:
                condition = ModelCardRow.domain.like(f"{spec.value}%")
            if spec.negated:
                condition = sa.not_(condition)
            return condition

        return inner

    @staticmethod
    def by_domain_ends_with(spec: StringMatchSpec) -> QueryCondition:
        def inner() -> sa.sql.expression.ColumnElement[bool]:
            if spec.case_insensitive:
                condition = ModelCardRow.domain.ilike(f"%{spec.value}")
            else:
                condition = ModelCardRow.domain.like(f"%{spec.value}")
            if spec.negated:
                condition = sa.not_(condition)
            return condition

        return inner

    by_domain_in = staticmethod(make_string_in_factory(ModelCardRow.domain))

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
        """Cursor condition for forward pagination (after cursor).

        Reads the cursor row's ``created_at`` and compares against that, because ``created_at`` is what
        the page is ordered by — comparing ids would draw the page boundary on a column the
        result is not sorted by.
        """
        cursor_uuid = uuid.UUID(cursor_id)

        def inner() -> sa.sql.expression.ColumnElement[bool]:
            subquery = (
                sa.select(ModelCardRow.created_at)
                .where(ModelCardRow.id == cursor_uuid)
                .scalar_subquery()
            )
            return ModelCardRow.created_at < subquery

        return inner

    @staticmethod
    def by_cursor_backward(cursor_id: str) -> QueryCondition:
        """Cursor condition for backward pagination (before cursor).

        Reads the cursor row's ``created_at`` and compares against that, because ``created_at`` is what
        the page is ordered by — comparing ids would draw the page boundary on a column the
        result is not sorted by.
        """
        cursor_uuid = uuid.UUID(cursor_id)

        def inner() -> sa.sql.expression.ColumnElement[bool]:
            subquery = (
                sa.select(ModelCardRow.created_at)
                .where(ModelCardRow.id == cursor_uuid)
                .scalar_subquery()
            )
            return ModelCardRow.created_at > subquery

        return inner
