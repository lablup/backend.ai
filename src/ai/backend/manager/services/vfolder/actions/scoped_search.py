"""VFolder search over the scopes vfolders are reachable from."""

from __future__ import annotations

from abc import ABC
from collections.abc import Sequence
from dataclasses import dataclass
from typing import override

from ai.backend.common.data.entity.project import ProjectID
from ai.backend.common.data.entity.types import EntityIdentifier, EntityType
from ai.backend.common.data.entity.user import UserID
from ai.backend.common.data.entity.vfolder import VFolderEntityType
from ai.backend.manager.actions.v2.ops.base import OperationScopeOpsAction, ScopeItem
from ai.backend.manager.data.vfolder.types import VFolderData
from ai.backend.manager.models.scopes import OperationScope
from ai.backend.manager.models.vfolder.row import VFolderRow
from ai.backend.manager.models.vfolder.scopes import (
    ProjectVFolderOperationScope,
    UserVFolderOperationScope,
)
from ai.backend.manager.models.vfolder.searchers import VFolderSearcher

__all__ = (
    "ProjectVFolderScopeItem",
    "ScopedSearchVFoldersAction",
    "UserVFolderScopeItem",
    "VFolderScopeItem",
)


class VFolderScopeItem(ScopeItem, ABC):
    """One side a vfolder is reachable from."""


@dataclass(frozen=True)
class ProjectVFolderScopeItem(VFolderScopeItem):
    """The vfolders of one project."""

    project_id: ProjectID

    @override
    def scope_id(self) -> EntityIdentifier:
        return self.project_id

    @override
    def operation_scope(self) -> OperationScope:
        return ProjectVFolderOperationScope(project_id=self.project_id)


@dataclass(frozen=True)
class UserVFolderScopeItem(VFolderScopeItem):
    """The vfolders one user reaches."""

    user_id: UserID

    @override
    def scope_id(self) -> EntityIdentifier:
        return self.user_id

    @override
    def operation_scope(self) -> OperationScope:
        return UserVFolderOperationScope(user_id=self.user_id)


@dataclass(frozen=True)
class ScopedSearchVFoldersAction(OperationScopeOpsAction[VFolderRow, VFolderData]):
    """Page through the vfolders the named scopes reach, combined with OR.

    Every scope is authorized before the read runs, so a caller reaching for one they
    cannot see is refused rather than served the rest.
    """

    items: Sequence[VFolderScopeItem]
    searcher: VFolderSearcher

    @override
    @classmethod
    def entity_type(cls) -> EntityType:
        return VFolderEntityType()

    @override
    @classmethod
    def action_name(cls) -> str:
        return "scoped_search_vfolders"

    @override
    def scope_targets(self) -> Sequence[EntityIdentifier]:
        return [item.scope_id() for item in self.items]

    @override
    def operation_scopes(self) -> Sequence[OperationScope]:
        return [item.operation_scope() for item in self.items]

    @override
    def to_searcher(self) -> VFolderSearcher:
        return self.searcher
