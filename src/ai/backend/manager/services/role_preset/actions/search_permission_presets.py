from __future__ import annotations

from dataclasses import dataclass
from typing import override

from ai.backend.common.data.entity.role_preset import ROLE_PRESET_ENTITY_TYPE
from ai.backend.common.data.entity.types import EntityType
from ai.backend.manager.actions.v2.ops.base import SearchGlobalOpsAction
from ai.backend.manager.data.role_preset.types import RolePermissionPresetData
from ai.backend.manager.models.rbac_models.role_permission_preset.row import (
    RolePermissionPresetRow,
)
from ai.backend.manager.repositories.role_preset.searchers import (
    RolePermissionPresetSearcher,
)


@dataclass
class SearchRolePermissionPresetsAction(
    SearchGlobalOpsAction[RolePermissionPresetRow, RolePermissionPresetData]
):
    """Page through the permission entries of the preset catalog."""

    searcher: RolePermissionPresetSearcher

    @override
    @classmethod
    def entity_type(cls) -> EntityType:
        return ROLE_PRESET_ENTITY_TYPE

    @override
    @classmethod
    def action_name(cls) -> str:
        return "search_role_permission_presets"

    @override
    def to_searcher(self) -> RolePermissionPresetSearcher:
        return self.searcher
