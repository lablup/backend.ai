"""Query conditions and orders for deployment revisions."""

from __future__ import annotations

import uuid
from collections.abc import Collection

import sqlalchemy as sa

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
    def by_name_equals(value: str, case_insensitive: bool = False) -> QueryCondition:
        def inner() -> sa.sql.expression.ColumnElement[bool]:
            if case_insensitive:
                return sa.func.lower(DeploymentRevisionRow.name) == value.lower()
            return DeploymentRevisionRow.name == value

        return inner

    @staticmethod
    def by_name_contains(value: str, case_insensitive: bool = False) -> QueryCondition:
        def inner() -> sa.sql.expression.ColumnElement[bool]:
            if case_insensitive:
                return sa.func.lower(DeploymentRevisionRow.name).contains(value.lower())
            return DeploymentRevisionRow.name.contains(value)

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
            return DeploymentRevisionRow.name.asc()
        else:
            return DeploymentRevisionRow.name.desc()

    @staticmethod
    def created_at(ascending: bool = True) -> QueryOrder:
        if ascending:
            return DeploymentRevisionRow.created_at.asc()
        else:
            return DeploymentRevisionRow.created_at.desc()
