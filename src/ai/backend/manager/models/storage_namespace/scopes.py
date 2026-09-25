"""Operation scopes for storage namespaces."""

from __future__ import annotations

from collections.abc import Sequence
from dataclasses import dataclass
from typing import Any, override

import sqlalchemy as sa

from ai.backend.common.data.entity.object_storage import ObjectStorageID
from ai.backend.common.data.entity.types import EntityIdentifier
from ai.backend.manager.models.clauses import QueryCondition
from ai.backend.manager.models.scopes import ExistenceCheck, ScopeTarget
from ai.backend.manager.models.storage_namespace.row import StorageNamespaceRow

__all__ = ("ObjectStorageNamespaceTarget",)


@dataclass(frozen=True)
class ObjectStorageNamespaceTarget(ScopeTarget):
    """The namespaces one object storage holds."""

    storage_id: ObjectStorageID

    @override
    def scope_id(self) -> EntityIdentifier:
        return self.storage_id

    @override
    def to_condition(self) -> QueryCondition:
        storage_id = self.storage_id

        def inner() -> sa.sql.expression.ColumnElement[bool]:
            return StorageNamespaceRow.storage_id == storage_id

        return inner

    @property
    @override
    def existence_checks(self) -> Sequence[ExistenceCheck[Any]]:
        return ()
