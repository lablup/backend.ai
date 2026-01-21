from __future__ import annotations

import uuid
from collections.abc import Collection

import sqlalchemy as sa

from ai.backend.manager.models.object_storage import ObjectStorageRow
from ai.backend.manager.repositories.base import QueryCondition


class ObjectStorageConditions:
    """Query conditions for object storages."""

    @staticmethod
    def by_ids(storage_ids: Collection[uuid.UUID]) -> QueryCondition:
        def inner() -> sa.sql.expression.ColumnElement[bool]:
            return ObjectStorageRow.id.in_(storage_ids)

        return inner
