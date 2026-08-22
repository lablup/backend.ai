from __future__ import annotations

from dataclasses import dataclass
from typing import override

from ai.backend.manager.actions.types import ActionOperationType
from ai.backend.manager.data.vfolder.types import VFolderData
from ai.backend.manager.repositories.base import BatchQuerier
from ai.backend.manager.services.vfolder.actions.base import VFolderGlobalAction


@dataclass
class GlobalSearchVFoldersAction(VFolderGlobalAction):
    """Page through vfolders across every scope."""

    querier: BatchQuerier

    @override
    @classmethod
    def operation_type(cls) -> ActionOperationType:
        return ActionOperationType.SEARCH

    @override
    @classmethod
    def action_name(cls) -> str:
        return "global_search_vfolders"


@dataclass
class GlobalSearchVFoldersActionResult:
    data: list[VFolderData]
    total_count: int
    has_next_page: bool
    has_previous_page: bool
