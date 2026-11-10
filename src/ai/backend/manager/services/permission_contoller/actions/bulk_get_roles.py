from __future__ import annotations

from collections.abc import Sequence
from dataclasses import dataclass, replace
from typing import Self, override

from ai.backend.common.data.entity.role import RoleID
from ai.backend.common.data.entity.types import EntityIdentifier
from ai.backend.manager.actions.v2.ops.base import PartialBulkGetEntityOpsAction
from ai.backend.manager.data.permission.role import RoleData
from ai.backend.manager.models.rbac_models.role.queriers import BulkRoleQuerier
from ai.backend.manager.models.rbac_models.role.row import RoleRow


@dataclass
class BulkGetRolesAction(PartialBulkGetEntityOpsAction[RoleRow, RoleData]):
    """Read the roles the caller named, answering for each id."""

    ids: Sequence[RoleID]

    @override
    @classmethod
    def action_name(cls) -> str:
        return "bulk_get_roles"

    @override
    def entity_ids(self) -> Sequence[EntityIdentifier]:
        return tuple(self.ids)

    @override
    def to_querier(self) -> BulkRoleQuerier:
        return BulkRoleQuerier()

    @override
    def narrowed_to(self, entity_ids: Sequence[EntityIdentifier]) -> Self:
        allowed = frozenset(entity_ids)
        return replace(self, ids=[entity_id for entity_id in self.ids if entity_id in allowed])
