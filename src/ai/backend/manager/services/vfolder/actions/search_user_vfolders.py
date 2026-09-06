from __future__ import annotations

import uuid
from collections.abc import Sequence
from dataclasses import dataclass
from typing import override

from ai.backend.common.data.entity.types import ScopeRef
from ai.backend.common.data.entity.user import USER_SCOPE_TYPE
from ai.backend.manager.actions.types import ActionOperationType
from ai.backend.manager.data.vfolder.types import VFolderData
from ai.backend.manager.models.vfolder.scopes import UserVFolderOperationScope
from ai.backend.manager.repositories.base import BatchQuerier
from ai.backend.manager.services.vfolder.actions.base import (
    VFolderScopeAction,
    VFolderScopeActionResult,
)


@dataclass
class SearchUserVFoldersAction(VFolderScopeAction):
    """Search vfolders owned by a specific user.

    RBAC validation checks if the user has READ permission in USER scope.
    Used for "my vfolders" page.
    """

    scope: UserVFolderOperationScope
    querier: BatchQuerier

    @override
    def scope_targets(self) -> Sequence[ScopeRef]:
        return (ScopeRef(scope_type=USER_SCOPE_TYPE, scope_id=self.scope.user_id),)

    @override
    @classmethod
    def operation_type(cls) -> ActionOperationType:
        return ActionOperationType.SEARCH

    @override
    @classmethod
    def action_name(cls) -> str:
        return "search_user_vfolders"


@dataclass
class SearchUserVFoldersActionResult(VFolderScopeActionResult):
    user_id: uuid.UUID
    data: list[VFolderData]
    total_count: int
    has_next_page: bool
    has_previous_page: bool
