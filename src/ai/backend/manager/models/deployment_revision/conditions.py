"""Query conditions for deployment revision repository."""

from __future__ import annotations

import uuid
from collections.abc import Collection
from datetime import datetime

import sqlalchemy as sa

from ai.backend.common.data.filter_specs import (
    StringMatchSpec,
    UUIDEqualMatchSpec,
    UUIDInMatchSpec,
)
from ai.backend.manager.models.clauses import QueryCondition
from ai.backend.manager.models.condition_utils import (
    make_int_conditions,
    make_string_in_factory,
)
from ai.backend.manager.models.deployment_revision import DeploymentRevisionRow


class RevisionConditions:
    """Query conditions for revisions."""

    @staticmethod
    def by_ids(revision_ids: Collection[uuid.UUID]) -> QueryCondition:
        def inner() -> sa.sql.expression.ColumnElement[bool]:
            return DeploymentRevisionRow.id.in_(revision_ids)

        return inner

    @staticmethod
    def by_deployment_id(deployment_id: uuid.UUID) -> QueryCondition:
        def inner() -> sa.sql.expression.ColumnElement[bool]:
            return DeploymentRevisionRow.endpoint == deployment_id

        return inner

    by_revision_number = make_int_conditions(DeploymentRevisionRow.revision_number)

    @staticmethod
    def by_image_filter_equals(spec: UUIDEqualMatchSpec) -> QueryCondition:
        def inner() -> sa.sql.expression.ColumnElement[bool]:
            if spec.negated:
                return DeploymentRevisionRow.image != spec.value
            return DeploymentRevisionRow.image == spec.value

        return inner

    @staticmethod
    def by_image_filter_in(spec: UUIDInMatchSpec) -> QueryCondition:
        def inner() -> sa.sql.expression.ColumnElement[bool]:
            if spec.negated:
                return DeploymentRevisionRow.image.notin_(spec.values)
            return DeploymentRevisionRow.image.in_(spec.values)

        return inner

    @staticmethod
    def by_model_vfolder_filter_equals(spec: UUIDEqualMatchSpec) -> QueryCondition:
        def inner() -> sa.sql.expression.ColumnElement[bool]:
            if spec.negated:
                return DeploymentRevisionRow.model != spec.value
            return DeploymentRevisionRow.model == spec.value

        return inner

    @staticmethod
    def by_model_vfolder_filter_in(spec: UUIDInMatchSpec) -> QueryCondition:
        def inner() -> sa.sql.expression.ColumnElement[bool]:
            if spec.negated:
                return DeploymentRevisionRow.model.notin_(spec.values)
            return DeploymentRevisionRow.model.in_(spec.values)

        return inner

    by_resource_group_in = staticmethod(
        make_string_in_factory(DeploymentRevisionRow.resource_group)
    )
    by_cluster_mode_in = staticmethod(make_string_in_factory(DeploymentRevisionRow.cluster_mode))

    @staticmethod
    def by_resource_group_equals(spec: StringMatchSpec) -> QueryCondition:
        def inner() -> sa.sql.expression.ColumnElement[bool]:
            if spec.case_insensitive:
                condition = (
                    sa.func.lower(DeploymentRevisionRow.resource_group) == spec.value.lower()
                )
            else:
                condition = DeploymentRevisionRow.resource_group == spec.value
            if spec.negated:
                condition = sa.not_(condition)
            return condition

        return inner

    @staticmethod
    def by_resource_group_contains(spec: StringMatchSpec) -> QueryCondition:
        def inner() -> sa.sql.expression.ColumnElement[bool]:
            if spec.case_insensitive:
                condition = DeploymentRevisionRow.resource_group.ilike(f"%{spec.value}%")
            else:
                condition = DeploymentRevisionRow.resource_group.like(f"%{spec.value}%")
            if spec.negated:
                condition = sa.not_(condition)
            return condition

        return inner

    @staticmethod
    def by_resource_group_starts_with(spec: StringMatchSpec) -> QueryCondition:
        def inner() -> sa.sql.expression.ColumnElement[bool]:
            if spec.case_insensitive:
                condition = DeploymentRevisionRow.resource_group.ilike(f"{spec.value}%")
            else:
                condition = DeploymentRevisionRow.resource_group.like(f"{spec.value}%")
            if spec.negated:
                condition = sa.not_(condition)
            return condition

        return inner

    @staticmethod
    def by_resource_group_ends_with(spec: StringMatchSpec) -> QueryCondition:
        def inner() -> sa.sql.expression.ColumnElement[bool]:
            if spec.case_insensitive:
                condition = DeploymentRevisionRow.resource_group.ilike(f"%{spec.value}")
            else:
                condition = DeploymentRevisionRow.resource_group.like(f"%{spec.value}")
            if spec.negated:
                condition = sa.not_(condition)
            return condition

        return inner

    @staticmethod
    def by_cluster_mode_equals(spec: StringMatchSpec) -> QueryCondition:
        def inner() -> sa.sql.expression.ColumnElement[bool]:
            if spec.case_insensitive:
                condition = sa.func.lower(DeploymentRevisionRow.cluster_mode) == spec.value.lower()
            else:
                condition = DeploymentRevisionRow.cluster_mode == spec.value
            if spec.negated:
                condition = sa.not_(condition)
            return condition

        return inner

    @staticmethod
    def by_cluster_mode_contains(spec: StringMatchSpec) -> QueryCondition:
        def inner() -> sa.sql.expression.ColumnElement[bool]:
            if spec.case_insensitive:
                condition = DeploymentRevisionRow.cluster_mode.ilike(f"%{spec.value}%")
            else:
                condition = DeploymentRevisionRow.cluster_mode.like(f"%{spec.value}%")
            if spec.negated:
                condition = sa.not_(condition)
            return condition

        return inner

    @staticmethod
    def by_cluster_mode_starts_with(spec: StringMatchSpec) -> QueryCondition:
        def inner() -> sa.sql.expression.ColumnElement[bool]:
            if spec.case_insensitive:
                condition = DeploymentRevisionRow.cluster_mode.ilike(f"{spec.value}%")
            else:
                condition = DeploymentRevisionRow.cluster_mode.like(f"{spec.value}%")
            if spec.negated:
                condition = sa.not_(condition)
            return condition

        return inner

    @staticmethod
    def by_cluster_mode_ends_with(spec: StringMatchSpec) -> QueryCondition:
        def inner() -> sa.sql.expression.ColumnElement[bool]:
            if spec.case_insensitive:
                condition = DeploymentRevisionRow.cluster_mode.ilike(f"%{spec.value}")
            else:
                condition = DeploymentRevisionRow.cluster_mode.like(f"%{spec.value}")
            if spec.negated:
                condition = sa.not_(condition)
            return condition

        return inner

    @staticmethod
    def by_created_at_before(dt: datetime) -> QueryCondition:
        def inner() -> sa.sql.expression.ColumnElement[bool]:
            return DeploymentRevisionRow.created_at < dt

        return inner

    @staticmethod
    def by_created_at_after(dt: datetime) -> QueryCondition:
        def inner() -> sa.sql.expression.ColumnElement[bool]:
            return DeploymentRevisionRow.created_at > dt

        return inner

    @staticmethod
    def by_created_at_equals(dt: datetime) -> QueryCondition:
        def inner() -> sa.sql.expression.ColumnElement[bool]:
            return DeploymentRevisionRow.created_at == dt

        return inner

    @staticmethod
    def by_cursor_forward(cursor_id: str) -> QueryCondition:
        """Cursor condition for forward pagination (after cursor).

        Uses subquery to get created_at of the cursor row and compare.
        """
        cursor_uuid = uuid.UUID(cursor_id)

        def inner() -> sa.sql.expression.ColumnElement[bool]:
            subquery = (
                sa.select(DeploymentRevisionRow.created_at)
                .where(DeploymentRevisionRow.id == cursor_uuid)
                .scalar_subquery()
            )
            return DeploymentRevisionRow.created_at < subquery

        return inner

    @staticmethod
    def by_cursor_backward(cursor_id: str) -> QueryCondition:
        """Cursor condition for backward pagination (before cursor).

        Uses subquery to get created_at of the cursor row and compare.
        """
        cursor_uuid = uuid.UUID(cursor_id)

        def inner() -> sa.sql.expression.ColumnElement[bool]:
            subquery = (
                sa.select(DeploymentRevisionRow.created_at)
                .where(DeploymentRevisionRow.id == cursor_uuid)
                .scalar_subquery()
            )
            return DeploymentRevisionRow.created_at > subquery

        return inner
