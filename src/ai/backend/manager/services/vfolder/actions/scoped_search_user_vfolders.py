"""Search of the pairs of one user and the vfolders the named scopes reach."""

from __future__ import annotations

from collections.abc import Sequence
from dataclasses import dataclass
from typing import override

from ai.backend.common.data.entity.types import EntityIdentifier, EntityType
from ai.backend.common.data.entity.user import UserID
from ai.backend.common.data.entity.vfolder import VFolderEntityType
from ai.backend.manager.actions.types import ActionOperationType
from ai.backend.manager.actions.v2.scope.base import BaseScopeAction
from ai.backend.manager.actions.v2.scope.result import BaseScopeActionResult
from ai.backend.manager.data.vfolder.types import UserVFolderData, VFolderData
from ai.backend.manager.models.specs.searcher import ScopedSearcher
from ai.backend.manager.models.vfolder.row import VFolderRow

__all__ = (
    "ScopedSearchUserVFoldersAction",
    "ScopedSearchUserVFoldersActionResult",
)


@dataclass(frozen=True)
class ScopedSearchUserVFoldersAction(BaseScopeAction):
    """Page through the vfolders the named scopes reach, each paired with one user.

    Every scope is authorized before the read runs, so a caller reaching for one they
    cannot see is rejected rather than served the rest.
    """

    user_id: UserID
    searcher: ScopedSearcher[VFolderRow, VFolderData]

    @override
    @classmethod
    def entity_type(cls) -> EntityType:
        return VFolderEntityType()

    @override
    @classmethod
    def operation_type(cls) -> ActionOperationType:
        return ActionOperationType.SEARCH

    @override
    @classmethod
    def action_name(cls) -> str:
        return "scoped_search_user_vfolders"

    @override
    def scope_targets(self) -> Sequence[EntityIdentifier]:
        return [scope.scope_id() for scope in self.searcher.scopes]


@dataclass(frozen=True)
class ScopedSearchUserVFoldersActionResult(BaseScopeActionResult):
    """A page of pairs. What the read reached is the vfolders of the pairs."""

    items: list[UserVFolderData]
    total_count: int
    has_next_page: bool
    has_previous_page: bool

    @override
    def entity_ids(self) -> Sequence[EntityIdentifier]:
        return [item.vfolder_id for item in self.items]
