from __future__ import annotations

from collections.abc import Sequence
from dataclasses import dataclass
from typing import override

from ai.backend.common.data.entity.role import RoleID
from ai.backend.common.data.entity.types import EntityIdentifier
from ai.backend.manager.actions.v2.ops.base import BulkScopedSearchOpsAction
from ai.backend.manager.data.permission.permission import PermissionData
from ai.backend.manager.models.rbac_models.permission.permission import PermissionRow
from ai.backend.manager.models.rbac_models.permission.scopes import PermissionOperationScope
from ai.backend.manager.models.rbac_models.permission.searchers import RolePermissionSearcher
from ai.backend.manager.models.scopes import OperationScope


@dataclass
class SearchRolePermissionsAction(BulkScopedSearchOpsAction[PermissionRow, PermissionData]):
    """Page through the permission entries the named roles hold, combined with OR."""

    role_ids: Sequence[RoleID]
    searcher: RolePermissionSearcher

    @override
    @classmethod
    def action_name(cls) -> str:
        return "search_role_permissions"

    @override
    def entity_ids(self) -> Sequence[EntityIdentifier]:
        return list(self.role_ids)

    @override
    def operation_scopes(self) -> Sequence[OperationScope]:
        return [PermissionOperationScope(role_id=role_id) for role_id in self.role_ids]

    @override
    def to_searcher(self) -> RolePermissionSearcher:
        return self.searcher
