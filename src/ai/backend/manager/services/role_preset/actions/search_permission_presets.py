from __future__ import annotations

from collections.abc import Sequence
from dataclasses import dataclass
from typing import override

from ai.backend.common.data.entity.role_preset import ROLE_PRESET_ENTITY_TYPE, RolePresetID
from ai.backend.common.data.entity.types import EntityType, ScopeRef, ScopeType
from ai.backend.manager.actions.v2.ops.base import OperationScopeOpsAction
from ai.backend.manager.data.role_preset.types import RolePermissionPresetData
from ai.backend.manager.models.rbac_models.role_permission_preset.row import (
    RolePermissionPresetRow,
)
from ai.backend.manager.models.scopes import OperationScope
from ai.backend.manager.repositories.role_preset.searchers import (
    RolePermissionPresetSearcher,
)
from ai.backend.manager.repositories.role_preset.types import (
    RolePresetPermissionOperationScope,
)


@dataclass
class SearchRolePermissionPresetsAction(
    OperationScopeOpsAction[RolePermissionPresetRow, RolePermissionPresetData]
):
    """Page through the permission entries inside one preset.

    The preset is the scope, so ops applies that condition and a caller-supplied
    filter can only narrow within it.
    """

    preset_id: RolePresetID
    searcher: RolePermissionPresetSearcher

    @override
    @classmethod
    def entity_type(cls) -> EntityType:
        return ROLE_PRESET_ENTITY_TYPE

    @override
    def scope_targets(self) -> Sequence[ScopeRef]:
        return (ScopeRef(scope_type=ScopeType(ROLE_PRESET_ENTITY_TYPE), scope_id=self.preset_id),)

    @override
    def operation_scopes(self) -> Sequence[OperationScope]:
        return (RolePresetPermissionOperationScope(preset_id=self.preset_id),)

    @override
    @classmethod
    def action_name(cls) -> str:
        return "search_role_permission_presets"

    @override
    def to_searcher(self) -> RolePermissionPresetSearcher:
        return self.searcher
