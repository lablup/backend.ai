"""Write specs for a role preset and the permission entries it carries.

A preset goes in through the creator alone, in the global scope, so no role is derived
from it.
"""

from __future__ import annotations

from dataclasses import dataclass
from typing import override

from ai.backend.common.data.entity.project import ProjectEntityType
from ai.backend.common.data.entity.role_preset import RolePresetID, RolePresetScopeID
from ai.backend.common.data.entity.types import EntityType
from ai.backend.manager.data.permission.types import Permission
from ai.backend.manager.data.role_preset.types import RolePermissionPresetData, RolePresetData
from ai.backend.manager.models.rbac_models.role_permission_preset.creators import (
    RolePermissionPresetCreator,
)
from ai.backend.manager.models.rbac_models.role_preset.creators import RolePresetCreator
from ai.backend.testutils.scenario_steps import Says
from bai_scenario.seeds.seeder import Naming, TestSeedFieldCreator, TestSeedRow


@dataclass(frozen=True)
class TestSeedRolePreset(TestSeedRow[RolePresetData]):
    """A role preset in the global catalog, carrying no permission entry. Without
    ``scope_id`` it is for every scope of ``scope_type``; with one, for that scope alone."""

    name_hint: str = "preset"
    scope_type: EntityType = ProjectEntityType()
    scope_id: RolePresetScopeID | None = None
    auto_assign: bool = False
    auto_assign_to_owner: bool = False
    role_name_template: str | None = None

    @override
    def kind(self) -> str:
        return Says("역할 프리셋", english="Role preset")

    @override
    def detail(self) -> str:
        if self.scope_id is not None:
            scope_ko = f"{self.scope_type} 스코프 하나용"
            scope_en = f"for one {self.scope_type} scope"
        elif self.scope_type == ProjectEntityType():
            scope_ko, scope_en = "프로젝트 스코프용", "for the project scope"
        else:
            scope_ko = f"{self.scope_type} 스코프용"
            scope_en = f"for the {self.scope_type} scope"
        notes_ko = ["자동 부여를 켬" if self.auto_assign else "자동 부여는 비활성"]
        notes_en = [
            "with automatic grant enabled" if self.auto_assign else "with automatic grant disabled"
        ]
        if self.auto_assign_to_owner:
            notes_ko.append("소유자 부여를 켬")
            notes_en.append("with owner assignment enabled")
        if self.role_name_template is not None:
            notes_ko.append("역할 이름 템플릿을 가짐")
            notes_en.append("carrying a role name template")
        return Says(
            f"{scope_ko}이고 {', '.join(notes_ko)}입니다",
            english=f"{scope_en}, {', '.join(notes_en)}",
        )

    @override
    def name(self, naming: Naming) -> str:
        return naming(self.name_hint)

    @override
    def seed(self, name: str) -> RolePresetCreator:
        return RolePresetCreator(
            name=name,
            scope_type=self.scope_type,
            scope_id=self.scope_id,
            auto_assign=self.auto_assign,
            auto_assign_to_owner=self.auto_assign_to_owner,
            role_name_template=self.role_name_template,
        )


@dataclass(frozen=True)
class TestSeedRolePresetPermission(TestSeedFieldCreator[RolePresetData, RolePermissionPresetData]):
    """One permission entry of the preset it is added to."""

    entity_type: EntityType
    permission: Permission

    @override
    def kind(self) -> str:
        permission = self.permission.name or int(self.permission)
        return Says(
            f"{self.entity_type} 전체에 {permission} 허용",
            english=f"{permission} allowed on every {self.entity_type}",
        )

    @override
    def owner_id(self, owner: RolePresetData) -> RolePresetID:
        return owner.id

    @override
    def seed(self) -> RolePermissionPresetCreator:
        return RolePermissionPresetCreator(entity_type=self.entity_type, permission=self.permission)
