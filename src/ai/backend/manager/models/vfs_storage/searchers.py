"""Searcher implementations for the VFS storage repository."""

from __future__ import annotations

from dataclasses import dataclass
from typing import Any, override

import sqlalchemy as sa

from ai.backend.manager.data.vfs_storage.types import VFSStorageData
from ai.backend.manager.models.specs.searcher import Searcher
from ai.backend.manager.models.vfs_storage.row import VFSStorageRow
from ai.backend.manager.models.vfs_storage.searchable_fields import (
    VFSStorageSearchableFields,
)


@dataclass
class VFSStorageSearcher(Searcher[VFSStorageRow, VFSStorageData]):
    @override
    def build_select(self) -> sa.sql.Select[Any]:
        return sa.select(VFSStorageRow)

    @override
    def to_data(self, row: VFSStorageRow) -> VFSStorageData:
        return VFSStorageSearchableFields.own.to_data(row)
