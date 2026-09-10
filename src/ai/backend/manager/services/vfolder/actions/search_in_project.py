from __future__ import annotations

import uuid
from collections.abc import Sequence
from dataclasses import dataclass
from typing import override

from ai.backend.common.data.entity.project import ProjectID
from ai.backend.common.data.entity.types import EntityIdentifier
from ai.backend.manager.actions.types import ActionOperationType
from ai.backend.manager.data.vfolder.types import VFolderData
from ai.backend.manager.models.vfolder.scopes import ProjectVFolderOperationScope
from ai.backend.manager.repositories.base import BatchQuerier
from ai.backend.manager.services.vfolder.actions.base import (
    VFolderScopeAction,
    VFolderScopeActionResult,
)


@dataclass
class SearchVFoldersInProjectAction(VFolderScopeAction):
    """Search vfolders within a project scope.

    RBAC validation checks if the user has READ permission in PROJECT scope.
    Used for project admin page.
    """

    scope: ProjectVFolderOperationScope
    querier: BatchQuerier

    @override
    def scope_targets(self) -> Sequence[EntityIdentifier]:
        return (ProjectID(self.scope.project_id),)

    @override
    @classmethod
    def operation_type(cls) -> ActionOperationType:
        return ActionOperationType.SEARCH

    @override
    @classmethod
    def action_name(cls) -> str:
        return "search_vfolders_in_project"


@dataclass
class SearchVFoldersInProjectActionResult(VFolderScopeActionResult):
    project_id: uuid.UUID
    data: list[VFolderData]
    total_count: int
    has_next_page: bool
    has_previous_page: bool
