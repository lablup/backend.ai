"""Write specs for a role and the permissions it carries.

A scenario states the permission it depends on rather than the name of a preset an
install ships. What the shipped presets grant is a different question, and answering it
here would make these rows break whenever that answer changed.
"""

from __future__ import annotations

from collections.abc import Callable
from dataclasses import dataclass
from typing import override

from ai.backend.common.data.entity.role import RoleID
from ai.backend.common.data.entity.types import EntityIdentifier, EntityType
from ai.backend.manager.data.permission.permission import PermissionData
from ai.backend.manager.data.permission.role import RoleData
from ai.backend.manager.data.permission.types import Permission
from ai.backend.manager.models.rbac_models.permission.creators import RolePermissionCreator
from ai.backend.manager.models.rbac_models.role.creators import RoleCreator
from ai.backend.testutils.scenario_steps import Says
from bai_scenario.seeds.seeder import Naming, TestSeedFieldCreator, TestSeedRowFrom


@dataclass(frozen=True)
class TestSeedRole[S](TestSeedRowFrom[S, RoleData]):
    """A custom role in the scope of the row it is given."""

    scope_of: Callable[[S], EntityIdentifier]
    name_hint: str = "role"

    @override
    def kind(self) -> str:
        return Says("역할", english="Role")

    @override
    def detail(self) -> str:
        return Says(
            "부여된 스코프 안에서만 적용됩니다",
            english="applies only within the scope it is granted in",
        )

    @override
    def name(self, naming: Naming) -> str:
        return naming(self.name_hint)

    @override
    def seed(self, name: str, source: S) -> RoleCreator:
        return RoleCreator(name=name, scope=self.scope_of(source))


@dataclass(frozen=True)
class TestSeedPermission(TestSeedFieldCreator[RoleData, PermissionData]):
    """One operation the role may perform on one entity type."""

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
    def owner_id(self, owner: RoleData) -> RoleID:
        return RoleID(owner.id)

    @override
    def seed(self) -> RolePermissionCreator:
        return RolePermissionCreator(entity_type=self.entity_type, permission=self.permission)
