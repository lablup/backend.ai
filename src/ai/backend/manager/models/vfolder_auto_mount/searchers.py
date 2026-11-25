from dataclasses import dataclass
from typing import Any, override

import sqlalchemy as sa

from ai.backend.common.data.entity.project import ProjectID
from ai.backend.common.data.entity.user import UserID
from ai.backend.common.data.vfolder_auto_mount.types import VFolderAutoMountScopeType
from ai.backend.manager.data.vfolder_auto_mount.types import VFolderAutoMountData
from ai.backend.manager.models.scopes import OperationScope
from ai.backend.manager.models.specs.orders.condition import ConditionOrder
from ai.backend.manager.models.specs.pagination import NoPagination
from ai.backend.manager.models.specs.searcher import Searcher
from ai.backend.manager.models.vfolder_auto_mount.row import VFolderAutoMountRow
from ai.backend.manager.models.vfolder_auto_mount.scopes import (
    ProjectVFolderAutoMountTarget,
    UserVFolderAutoMountTarget,
)
from ai.backend.manager.models.vfolder_auto_mount.searchable_fields import (
    VFolderAutoMountSearchableFields,
)


@dataclass
class VFolderAutoMountSearcher(Searcher[VFolderAutoMountRow, VFolderAutoMountData]):
    """Soft-deleted rows are included; filter on ``deleted_at`` to leave them out."""

    @override
    def build_select(self) -> sa.sql.Select[Any]:
        return sa.select(VFolderAutoMountRow)

    @override
    def to_data(self, row: VFolderAutoMountRow) -> VFolderAutoMountData:
        return VFolderAutoMountSearchableFields.own.to_data(row)


@dataclass(frozen=True)
class SessionVFolderAutoMountsSearch:
    """The live auto-mounts of a session's project and of its owner, the project's first.

    Run with ``search_with_scopes(operation_scopes(), searcher())``.
    """

    user_id: UserID
    project_id: ProjectID | None

    def operation_scopes(self) -> list[OperationScope]:
        scopes: list[OperationScope] = [UserVFolderAutoMountTarget(user_id=self.user_id)]
        if self.project_id is not None:
            scopes.append(ProjectVFolderAutoMountTarget(project_id=self.project_id))
        return scopes

    def searcher(self) -> VFolderAutoMountSearcher:
        own = VFolderAutoMountSearchableFields.own
        return VFolderAutoMountSearcher(
            pagination=NoPagination(),
            conditions=[own.deleted_at.filter.is_null()],
            orders=[
                ConditionOrder(
                    own.scope_type.filter.equals(VFolderAutoMountScopeType.PROJECT)
                ).first(),
                own.created_at.order.apply(ascending=True),
                own.id.order.apply(ascending=True),
            ],
        )
