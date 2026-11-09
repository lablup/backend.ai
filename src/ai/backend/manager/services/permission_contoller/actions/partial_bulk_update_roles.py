from collections.abc import Mapping, Sequence
from dataclasses import dataclass, replace
from typing import Self, override

from ai.backend.common.data.entity.types import EntityIdentifier
from ai.backend.manager.actions.v2.ops.base import UpdatePartialBulkOpsAction
from ai.backend.manager.data.permission.role import RoleData
from ai.backend.manager.models.rbac_models.role.row import RoleRow
from ai.backend.manager.models.rbac_models.role.updaters import RoleUpdater


@dataclass(frozen=True)
class PartialBulkUpdateRolesAction(UpdatePartialBulkOpsAction[RoleRow, RoleData]):
    """Edit the named roles' declarations, answering for each one."""

    updaters: Sequence[RoleUpdater]

    @override
    @classmethod
    def action_name(cls) -> str:
        return "partial_bulk_update_roles"

    @override
    def entity_ids(self) -> Sequence[EntityIdentifier]:
        return tuple(updater.role_id for updater in self.updaters)

    @override
    def to_updaters(self) -> Mapping[EntityIdentifier, RoleUpdater]:
        return {updater.role_id: updater for updater in self.updaters}

    @override
    def narrowed_to(self, entity_ids: Sequence[EntityIdentifier]) -> Self:
        allowed = frozenset(entity_ids)
        return replace(
            self, updaters=[updater for updater in self.updaters if updater.role_id in allowed]
        )
