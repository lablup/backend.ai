"""Searcher implementations for the storage namespace repository."""

from __future__ import annotations

from dataclasses import dataclass
from typing import Any, override

import sqlalchemy as sa

from ai.backend.manager.data.storage_namespace.types import StorageNamespaceData
from ai.backend.manager.models.specs.searcher import Searcher
from ai.backend.manager.models.storage_namespace.row import StorageNamespaceRow


@dataclass
class StorageNamespaceSearcher(Searcher[StorageNamespaceRow, StorageNamespaceData]):
    @override
    def build_select(self) -> sa.sql.Select[Any]:
        return sa.select(StorageNamespaceRow)

    @override
    def to_data(self, row: StorageNamespaceRow) -> StorageNamespaceData:
        return row.to_dataclass()
