"""Write specs for a role preset and the permission entries it carries.

A preset goes in through the creator alone, in the global scope, so no role is derived
from it.
"""

from __future__ import annotations

from dataclasses import dataclass
from typing import override

from ai.backend.common.data.entity.project import ProjectEntityType
from ai.backend.common.data.entity.role_preset import RolePresetID
from ai.backend.common.data.entity.types import EntityType
from ai.backend.manager.data.permission.types import Permission
from ai.backend.manager.data.role_preset.types import RolePermissionPresetData, RolePresetData
from ai.backend.manager.models.rbac_models.role_permission_preset.creators import (
    RolePermissionPresetCreator,
)
from ai.backend.manager.models.rbac_models.role_preset.creators import RolePresetCreator
from bai_scenario.seeds.seeder import Naming, TestSeedFieldCreator, TestSeedRow


@dataclass(frozen=True)
class TestSeedRolePreset(TestSeedRow[RolePresetData]):
    """A role preset in the global catalog, carrying no permission entry."""

    name_hint: str = "preset"

    @override
    def kind(self) -> str:
        return "역할 프리셋"

    @override
    def detail(self) -> str:
        return "프로젝트 스코프용이고 자동 부여는 꺼져 있다"

    @override
    def name(self, naming: Naming) -> str:
        return naming(self.name_hint)

    @override
    def seed(self, name: str) -> RolePresetCreator:
        return RolePresetCreator(name=name, scope_type=ProjectEntityType())


@dataclass(frozen=True)
class TestSeedRolePresetPermission(TestSeedFieldCreator[RolePresetData, RolePermissionPresetData]):
    """One permission entry of the preset it is added to."""

    entity_type: EntityType
    permission: Permission

    @override
    def kind(self) -> str:
        return f"{self.entity_type} 전체에 {self.permission.name or int(self.permission)} 허용 항목"

    @override
    def owner_id(self, owner: RolePresetData) -> RolePresetID:
        return owner.id

    @override
    def seed(self) -> RolePermissionPresetCreator:
        return RolePermissionPresetCreator(entity_type=self.entity_type, permission=self.permission)
