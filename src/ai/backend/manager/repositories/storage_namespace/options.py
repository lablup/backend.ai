from __future__ import annotations

import uuid
from collections.abc import Collection

import sqlalchemy as sa

from ai.backend.manager.models.storage_namespace import StorageNamespaceRow
from ai.backend.manager.repositories.base import QueryCondition


class StorageNamespaceConditions:
    """Query conditions for storage namespaces."""

    @staticmethod
    def by_ids(namespace_ids: Collection[uuid.UUID]) -> QueryCondition:
        def inner() -> sa.sql.expression.ColumnElement[bool]:
            return StorageNamespaceRow.id.in_(namespace_ids)

        return inner
