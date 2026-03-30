from __future__ import annotations

from dataclasses import dataclass
from typing import override

from ai.backend.manager.actions.action.base import BaseActionResult
from ai.backend.manager.actions.types import ActionOperationType
from ai.backend.manager.data.vfolder.types import VFolderData
from ai.backend.manager.repositories.base import BatchQuerier
from ai.backend.manager.services.vfolder.actions.base import VFolderAction


@dataclass
class AdminSearchVFoldersAction(VFolderAction):
    """Search all vfolders with filtering, ordering, and pagination.

    Admin-only action without scope restriction.
    """

    querier: BatchQuerier

    @override
    def entity_id(self) -> str | None:
        return None

    @override
    @classmethod
    def operation_type(cls) -> ActionOperationType:
        return ActionOperationType.SEARCH


@dataclass
class AdminSearchVFoldersActionResult(BaseActionResult):
    """Result of AdminSearchVFoldersAction."""

    data: list[VFolderData]
    total_count: int
    has_next_page: bool
    has_previous_page: bool

    @override
    def entity_id(self) -> str | None:
        return None
