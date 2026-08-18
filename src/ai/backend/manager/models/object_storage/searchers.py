"""Searcher implementations for the object storage repository."""

from __future__ import annotations

from dataclasses import dataclass
from typing import Any, override

import sqlalchemy as sa

from ai.backend.manager.data.object_storage.types import ObjectStorageData
from ai.backend.manager.models.object_storage.row import ObjectStorageRow
from ai.backend.manager.models.specs.searcher import Searcher


@dataclass
class ObjectStorageSearcher(Searcher[ObjectStorageRow, ObjectStorageData]):
    @override
    def build_select(self) -> sa.sql.Select[Any]:
        return sa.select(ObjectStorageRow)

    @override
    def to_data(self, row: ObjectStorageRow) -> ObjectStorageData:
        return row.to_dataclass()
