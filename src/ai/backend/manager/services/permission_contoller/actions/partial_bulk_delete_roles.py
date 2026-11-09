from collections.abc import Mapping, Sequence
from dataclasses import dataclass, replace
from typing import Self, override

from ai.backend.common.data.entity.role import RoleID
from ai.backend.common.data.entity.types import EntityIdentifier
from ai.backend.manager.actions.v2.ops.base import DeletePartialBulkOpsAction
from ai.backend.manager.data.permission.role import RoleData
from ai.backend.manager.models.rbac_models.role.row import RoleRow
from ai.backend.manager.models.rbac_models.role.updaters import RoleSoftDeleteUpdater


@dataclass(frozen=True)
class PartialBulkDeleteRolesAction(DeletePartialBulkOpsAction[RoleRow, RoleData]):
    """Retire the named roles, answering for each one."""

    ids: Sequence[RoleID]

    @override
    @classmethod
    def action_name(cls) -> str:
        return "partial_bulk_delete_roles"

    @override
    def entity_ids(self) -> Sequence[EntityIdentifier]:
        return tuple(self.ids)

    @override
    def to_updaters(self) -> Mapping[EntityIdentifier, RoleSoftDeleteUpdater]:
        return {role_id: RoleSoftDeleteUpdater(role_id=role_id) for role_id in self.ids}

    @override
    def narrowed_to(self, entity_ids: Sequence[EntityIdentifier]) -> Self:
        allowed = frozenset(entity_ids)
        return replace(self, ids=[role_id for role_id in self.ids if role_id in allowed])
