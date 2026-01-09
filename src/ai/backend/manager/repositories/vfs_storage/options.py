from __future__ import annotations

import uuid
from collections.abc import Collection

import sqlalchemy as sa

from ai.backend.manager.models.vfs_storage import VFSStorageRow
from ai.backend.manager.repositories.base import QueryCondition


class VFSStorageConditions:
    """Query conditions for VFS storages."""

    @staticmethod
    def by_ids(storage_ids: Collection[uuid.UUID]) -> QueryCondition:
        def inner() -> sa.sql.expression.ColumnElement[bool]:
            return VFSStorageRow.id.in_(storage_ids)

        return inner
