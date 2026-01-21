from __future__ import annotations

from dataclasses import dataclass
from typing import Optional, override

from ai.backend.manager.actions.action import BaseActionResult
from ai.backend.manager.data.vfs_storage.types import VFSStorageData
from ai.backend.manager.repositories.base import BatchQuerier
from ai.backend.manager.services.vfs_storage.actions.base import VFSStorageAction


@dataclass
class SearchVFSStoragesAction(VFSStorageAction):
    """Action to search VFS storages."""

    querier: BatchQuerier

    @override
    @classmethod
    def operation_type(cls) -> str:
        return "search_vfs_storages"

    @override
    def entity_id(self) -> Optional[str]:
        return None


@dataclass
class SearchVFSStoragesActionResult(BaseActionResult):
    """Result of searching VFS storages."""

    storages: list[VFSStorageData]
    total_count: int
    has_next_page: bool
    has_previous_page: bool

    @override
    def entity_id(self) -> Optional[str]:
        return None
