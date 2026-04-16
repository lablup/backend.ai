"""Query conditions for deployment revision repository."""

from __future__ import annotations

import uuid
from collections.abc import Collection

import sqlalchemy as sa

from ai.backend.manager.models.condition_utils import make_int_conditions
from ai.backend.manager.models.deployment_revision import DeploymentRevisionRow
from ai.backend.manager.repositories.base import QueryCondition


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
