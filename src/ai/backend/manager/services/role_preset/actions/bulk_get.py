from __future__ import annotations

from collections.abc import Sequence
from dataclasses import dataclass, replace
from typing import Self, override

from ai.backend.common.data.entity.role_preset import RolePresetID
from ai.backend.common.data.entity.types import EntityIdentifier
from ai.backend.manager.actions.v2.ops.base import PartialBulkGetEntityOpsAction
from ai.backend.manager.data.role_preset.types import RolePresetData
from ai.backend.manager.models.rbac_models.role_preset.queriers import BulkRolePresetQuerier
from ai.backend.manager.models.rbac_models.role_preset.row import RolePresetRow


@dataclass
class BulkGetRolePresetsAction(PartialBulkGetEntityOpsAction[RolePresetRow, RolePresetData]):
    """Read the role presets the caller named, one permission check per preset."""

    ids: Sequence[RolePresetID]

    @override
    @classmethod
    def action_name(cls) -> str:
        return "bulk_get_role_presets"

    @override
    def entity_ids(self) -> Sequence[EntityIdentifier]:
        return tuple(self.ids)

    @override
    def to_querier(self) -> BulkRolePresetQuerier:
        return BulkRolePresetQuerier()

    @override
    def narrowed_to(self, entity_ids: Sequence[EntityIdentifier]) -> Self:
        allowed = frozenset(entity_ids)
        return replace(self, ids=[entity_id for entity_id in self.ids if entity_id in allowed])
