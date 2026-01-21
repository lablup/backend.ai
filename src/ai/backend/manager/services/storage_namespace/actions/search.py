from __future__ import annotations

from dataclasses import dataclass
from typing import Optional, override

from ai.backend.manager.actions.action import BaseActionResult
from ai.backend.manager.data.storage_namespace.types import StorageNamespaceData
from ai.backend.manager.repositories.base import BatchQuerier
from ai.backend.manager.services.storage_namespace.actions.base import StorageNamespaceAction


@dataclass
class SearchStorageNamespacesAction(StorageNamespaceAction):
    """Action to search storage namespaces."""

    querier: BatchQuerier

    @override
    @classmethod
    def operation_type(cls) -> str:
        return "search"

    @override
    def entity_id(self) -> Optional[str]:
        return None


@dataclass
class SearchStorageNamespacesActionResult(BaseActionResult):
    """Result of searching storage namespaces."""

    namespaces: list[StorageNamespaceData]
    total_count: int
    has_next_page: bool
    has_previous_page: bool

    @override
    def entity_id(self) -> Optional[str]:
        return None
