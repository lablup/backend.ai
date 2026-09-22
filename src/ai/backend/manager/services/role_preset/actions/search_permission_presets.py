from __future__ import annotations

from collections.abc import Sequence
from dataclasses import dataclass
from typing import override

from ai.backend.common.data.entity.role_preset import RolePresetID
from ai.backend.common.data.entity.types import EntityIdentifier
from ai.backend.manager.actions.v2.ops.base import BulkScopedSearchOpsAction
from ai.backend.manager.data.role_preset.types import RolePermissionPresetData
from ai.backend.manager.models.rbac_models.role_permission_preset.row import (
    RolePermissionPresetRow,
)
from ai.backend.manager.models.rbac_models.role_permission_preset.scopes import (
    RolePresetPermissionTarget,
)
from ai.backend.manager.models.rbac_models.role_preset.searchers import (
    RolePermissionPresetSearcher,
)
from ai.backend.manager.models.scopes import OperationScope


@dataclass
class SearchRolePermissionPresetsAction(
    BulkScopedSearchOpsAction[RolePermissionPresetRow, RolePermissionPresetData]
):
    """Page through the permission entries the named presets hold, combined with OR.

    Every preset is authorized before the read runs.
    """

    preset_ids: Sequence[RolePresetID]
    searcher: RolePermissionPresetSearcher

    @override
    @classmethod
    def action_name(cls) -> str:
        return "search_role_permission_presets"

    @override
    def entity_ids(self) -> Sequence[EntityIdentifier]:
        return tuple(self.preset_ids)

    @override
    def operation_scopes(self) -> Sequence[OperationScope]:
        return [RolePresetPermissionTarget(preset_id=preset_id) for preset_id in self.preset_ids]

    @override
    def to_searcher(self) -> RolePermissionPresetSearcher:
        return self.searcher
