"""Query conditions and orders for deployment revisions."""

from __future__ import annotations

import uuid
from collections.abc import Collection
from typing import cast

import sqlalchemy as sa

from ai.backend.manager.api.gql.base import StringMatchSpec
from ai.backend.manager.models.deployment_revision import DeploymentRevisionRow
from ai.backend.manager.repositories.base import QueryCondition, QueryOrder


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

    @staticmethod
    def by_name_equals(spec: StringMatchSpec) -> QueryCondition:
        def inner() -> sa.sql.expression.ColumnElement[bool]:
            if spec.case_insensitive:
                condition = sa.func.lower(DeploymentRevisionRow.name) == spec.value.lower()
            else:
                condition = DeploymentRevisionRow.name == spec.value
            if spec.negated:
                condition = sa.not_(condition)
            return condition

        return inner

    @staticmethod
    def by_name_contains(spec: StringMatchSpec) -> QueryCondition:
        def inner() -> sa.sql.expression.ColumnElement[bool]:
            if spec.case_insensitive:
                condition = DeploymentRevisionRow.name.ilike(f"%{spec.value}%")
            else:
                condition = DeploymentRevisionRow.name.like(f"%{spec.value}%")
            if spec.negated:
                condition = sa.not_(condition)
            return cast(sa.sql.expression.ColumnElement[bool], condition)

        return inner

    @staticmethod
    def by_name_starts_with(spec: StringMatchSpec) -> QueryCondition:
        def inner() -> sa.sql.expression.ColumnElement[bool]:
            if spec.case_insensitive:
                condition = DeploymentRevisionRow.name.ilike(f"{spec.value}%")
            else:
                condition = DeploymentRevisionRow.name.like(f"{spec.value}%")
            if spec.negated:
                condition = sa.not_(condition)
            return cast(sa.sql.expression.ColumnElement[bool], condition)

        return inner

    @staticmethod
    def by_name_ends_with(spec: StringMatchSpec) -> QueryCondition:
        def inner() -> sa.sql.expression.ColumnElement[bool]:
            if spec.case_insensitive:
                condition = DeploymentRevisionRow.name.ilike(f"%{spec.value}")
            else:
                condition = DeploymentRevisionRow.name.like(f"%{spec.value}")
            if spec.negated:
                condition = sa.not_(condition)
            return cast(sa.sql.expression.ColumnElement[bool], condition)

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


class RevisionOrders:
    """Query orders for revisions."""

    @staticmethod
    def name(ascending: bool = True) -> QueryOrder:
        if ascending:
            return cast(QueryOrder, DeploymentRevisionRow.name.asc())
        return cast(QueryOrder, DeploymentRevisionRow.name.desc())

    @staticmethod
    def created_at(ascending: bool = True) -> QueryOrder:
        if ascending:
            return cast(QueryOrder, DeploymentRevisionRow.created_at.asc())
        return cast(QueryOrder, DeploymentRevisionRow.created_at.desc())
