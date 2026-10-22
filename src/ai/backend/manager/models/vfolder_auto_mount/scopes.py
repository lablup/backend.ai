from collections.abc import Sequence
from dataclasses import dataclass
from typing import Any, override

import sqlalchemy as sa

from ai.backend.common.data.entity.project import ProjectID
from ai.backend.common.data.entity.types import EntityIdentifier
from ai.backend.common.data.vfolder_auto_mount.types import VFolderAutoMountScopeType
from ai.backend.manager.models.clauses import QueryCondition
from ai.backend.manager.models.scopes import ExistenceCheck, ScopeTarget
from ai.backend.manager.models.vfolder_auto_mount.row import VFolderAutoMountRow


@dataclass(frozen=True)
class ProjectVFolderAutoMountTarget(ScopeTarget):
    """The auto-mounts set on one project, a personal project included."""

    project_id: ProjectID

    @override
    def scope_id(self) -> EntityIdentifier:
        return self.project_id

    @override
    def to_condition(self) -> QueryCondition:
        project_id = self.project_id

        def inner() -> sa.sql.expression.ColumnElement[bool]:
            return sa.and_(
                VFolderAutoMountRow.scope_type == VFolderAutoMountScopeType.PROJECT,
                VFolderAutoMountRow.scope_id == project_id,
            )

        return inner

    @property
    @override
    def existence_checks(self) -> Sequence[ExistenceCheck[Any]]:
        return ()
