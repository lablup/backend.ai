from __future__ import annotations

from dataclasses import dataclass
from typing import Optional, override

from ai.backend.manager.actions.action import BaseActionResult
from ai.backend.manager.data.object_storage.types import ObjectStorageData
from ai.backend.manager.repositories.base import BatchQuerier
from ai.backend.manager.services.object_storage.actions.base import ObjectStorageAction


@dataclass
class SearchObjectStoragesAction(ObjectStorageAction):
    """Action to search Object storages."""

    querier: BatchQuerier

    @override
    @classmethod
    def operation_type(cls) -> str:
        return "search_object_storages"

    @override
    def entity_id(self) -> Optional[str]:
        return None


@dataclass
class SearchObjectStoragesActionResult(BaseActionResult):
    """Result of searching Object storages."""

    storages: list[ObjectStorageData]
    total_count: int
    has_next_page: bool
    has_previous_page: bool

    @override
    def entity_id(self) -> Optional[str]:
        return None
