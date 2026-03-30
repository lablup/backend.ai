from __future__ import annotations

import uuid
from dataclasses import dataclass
from typing import override

from ai.backend.common.data.permission.types import RBACElementType, ScopeType
from ai.backend.manager.actions.types import ActionOperationType
from ai.backend.manager.data.permission.types import RBACElementRef
from ai.backend.manager.data.vfolder.types import VFolderData
from ai.backend.manager.repositories.base import BatchQuerier
from ai.backend.manager.repositories.vfolder.types import UserVFolderSearchScope
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

    scope: UserVFolderSearchScope
    querier: BatchQuerier

    @override
    def entity_id(self) -> str | None:
        return None

    @override
    @classmethod
    def operation_type(cls) -> ActionOperationType:
        return ActionOperationType.SEARCH

    @override
    def scope_type(self) -> ScopeType:
        return ScopeType.USER

    @override
    def scope_id(self) -> str:
        return str(self.scope.user_id)

    @override
    def target_element(self) -> RBACElementRef:
        return RBACElementRef(
            element_type=RBACElementType.USER,
            element_id=str(self.scope.user_id),
        )


@dataclass
class SearchUserVFoldersActionResult(VFolderScopeActionResult):
    user_id: uuid.UUID
    data: list[VFolderData]
    total_count: int
    has_next_page: bool
    has_previous_page: bool

    @override
    def scope_type(self) -> ScopeType:
        return ScopeType.USER

    @override
    def scope_id(self) -> str:
        return str(self.user_id)
