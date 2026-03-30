from __future__ import annotations

from dataclasses import dataclass
from typing import override

from ai.backend.manager.actions.action import BaseActionResult
from ai.backend.manager.actions.types import ActionOperationType
from ai.backend.manager.data.object_storage.types import ObjectStorageData
from ai.backend.manager.repositories.base import BatchQuerier
from ai.backend.manager.services.object_storage.actions.base import ObjectStorageAction


@dataclass
class SearchObjectStoragesAction(ObjectStorageAction):
    """Action to search Object storages."""

    querier: BatchQuerier

    @override
    @classmethod
    def operation_type(cls) -> ActionOperationType:
        return ActionOperationType.SEARCH

    @override
    def entity_id(self) -> str | None:
        return None


@dataclass
class SearchObjectStoragesActionResult(BaseActionResult):
    """Result of searching Object storages."""

    storages: list[ObjectStorageData]
    total_count: int
    has_next_page: bool
    has_previous_page: bool

    @override
    def entity_id(self) -> str | None:
        return None
