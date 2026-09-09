"""Write specs for a role and the permissions it carries.

A scenario states the permission it depends on rather than the name of a preset an
install ships. What the shipped presets grant is a different question, and answering it
here would make these rows break whenever that answer changed.
"""

from __future__ import annotations

from collections.abc import Callable

from ai.backend.common.data.entity.role import RoleID
from ai.backend.common.data.entity.types import EntityIdentifier, EntityType
from ai.backend.manager.data.permission.permission import PermissionData
from ai.backend.manager.data.permission.role import RoleData
from ai.backend.manager.data.permission.types import Permission
from ai.backend.manager.models.rbac_models.permission.creators import RolePermissionCreator
from ai.backend.manager.models.rbac_models.role.creators import RoleCreator
from bai_scenario.seeds.seeder import FieldOf, SpecFrom


def seed_role[S](
    scope_of: Callable[[S], EntityIdentifier], *, name_hint: str = "role"
) -> SpecFrom[S, RoleData]:
    """A custom role in the scope of the row it is given."""

    def build(name: str, scope: S) -> RoleCreator:
        return RoleCreator(name=name, scope=scope_of(scope))

    return SpecFrom(name_hint, build)


def seed_permission(
    *, entity_type: EntityType, permission: Permission
) -> FieldOf[RoleData, PermissionData]:
    """One operation the role may perform on one entity type."""
    return FieldOf(
        hint=f"{permission!s} on {entity_type}",
        owner_id=lambda role: RoleID(role.id),
        spec=RolePermissionCreator(entity_type=entity_type, permission=permission),
    )
