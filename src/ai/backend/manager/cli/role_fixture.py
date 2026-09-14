from __future__ import annotations

import json
import uuid
from collections.abc import Mapping, Sequence
from pathlib import Path
from typing import Any, Final

from ai.backend.common.data.entity.domain import DomainEntityType
from ai.backend.common.data.entity.project import ProjectEntityType
from ai.backend.common.data.entity.types import EntityType
from ai.backend.common.data.entity.user import UserEntityType
from ai.backend.common.data.permission.types import Permission
from ai.backend.manager.data.permission.seed.role import RoleSeed

# Every generated id is a uuid5 under this namespace, so the same declaration writes
# the same file.
_NAMESPACE: Final[uuid.UUID] = uuid.UUID("b6b0f7a4-1c1d-5a2f-9e3b-8c7d6a5f4e30")
_TIMESTAMP: Final[str] = "2025-09-12 09:51:58.265582+00"
# The operation names the legacy `role_permission_presets.operation` column takes.
_OPERATION_NAMES: Final[tuple[tuple[Permission, str], ...]] = (
    (Permission.READ, "read"),
    (Permission.UPDATE, "update"),
    (Permission.CREATE, "create"),
    (Permission.SOFT_DELETE, "soft-delete"),
    (Permission.HARD_DELETE, "hard-delete"),
)
# Which seed roles a user is assigned, by the role their account carries. A superadmin
# bypasses the RBAC check entirely, so it holds no scope role; a monitor holds none either.
_ASSIGNED: Final[Mapping[str, tuple[str, ...]]] = {
    "superadmin": ("user_owner",),
    "admin": ("user_owner", "domain_admin", "project_admin"),
    "user": ("user_owner", "project_member"),
    "monitor": ("user_owner",),
}


def _identify(*parts: str) -> str:
    return str(uuid.uuid5(_NAMESPACE, "|".join(parts)))


class RoleFixture:
    """Writes the seed fixture from the role files and the account fixtures.

    The role files give what each role is granted, the account fixtures give the users,
    projects and domain. Every row is derived from those two, and every id is a uuid5
    of what it identifies.
    """

    _seeds: Mapping[str, RoleSeed]
    _users: list[dict[str, Any]]
    _groups: list[dict[str, Any]]
    _domains: list[dict[str, Any]]
    _scope_entities: dict[tuple[str, str], str]
    _memberships: list[dict[str, str]]

    def __init__(self, seeds: Sequence[RoleSeed], fixtures: Path) -> None:
        self._seeds = {seed.name: seed for seed in seeds}
        accounts = json.loads((fixtures / "example-users.json").read_text(encoding="utf-8"))
        self._users = accounts["users"]
        self._groups = accounts["groups"]
        self._domains = accounts["domains"]
        self._scope_entities = {
            (entity["entity_type"], entity["entity_id"]): entity["id"]
            for entity in accounts["virtual_entities"]
        }
        self._memberships = accounts["association_groups_users"]

    def render(self) -> dict[str, Any]:
        roles = self._roles()
        return {
            "__generated_by": "backend.ai mgr permissions emit",
            "roles": [self._without_notes(role) for role in roles],
            "user_roles": self._user_roles(roles),
            "permissions": self._permissions(roles),
            "role_presets": self._presets(),
            "role_permission_presets": self._permission_presets(),
            "virtual_entities": self._virtual_entities(roles),
            "entity_memberships": self._entity_memberships(roles),
            "scope_bindings": self._scope_bindings(roles),
        }

    def _without_notes(self, row: Mapping[str, Any]) -> dict[str, Any]:
        """The row without the keys only this generator reads."""
        return {key: value for key, value in row.items() if not key.startswith("__")}

    def _domain(self) -> dict[str, Any]:
        return self._domains[0]

    def _accounts_in(self, group_id: str) -> list[dict[str, Any]]:
        joined = {row["user_id"] for row in self._memberships if row["group_id"] == group_id}
        return [user for user in self._users if user["uuid"] in joined]

    def _role_row(
        self, preset: str, scope_type: EntityType, scope_id: str, name: str, source: str
    ) -> dict[str, Any]:
        return {
            "id": _identify("role", str(scope_type), scope_id, name),
            "name": name,
            "scope_type": str(scope_type),
            "scope_id": scope_id,
            "description": "",
            "source": source,
            "status": "active",
            "auto_assign": self._seeds[preset].auto_assign,
            "created_at": _TIMESTAMP,
            "updated_at": _TIMESTAMP,
            "deleted_at": None,
            "__preset": preset,
        }

    def _roles(self) -> list[dict[str, Any]]:
        domain = self._domain()
        roles = [
            self._role_row(
                "domain_admin",
                DomainEntityType(),
                domain["id"],
                f"role_domain_{domain['name']}_admin",
                "system",
            )
        ]
        for group in self._groups:
            short = group["id"][:8]
            roles.append(
                self._role_row(
                    "project_admin",
                    ProjectEntityType(),
                    group["id"],
                    f"role_project_{short}_admin",
                    "system",
                )
            )
            roles.append(
                self._role_row(
                    "project_member",
                    ProjectEntityType(),
                    group["id"],
                    f"role_project_{short}_member",
                    "custom",
                )
            )
        for user in self._users:
            roles.append(
                self._role_row(
                    "user_owner",
                    UserEntityType(),
                    user["uuid"],
                    f"role_user_{user['username']}",
                    "system",
                )
            )
        return roles

    def _user_roles(self, roles: Sequence[dict[str, Any]]) -> list[dict[str, Any]]:
        by_scope = {
            (role["scope_type"], role["scope_id"], role["__preset"]): role for role in roles
        }
        assigned: list[dict[str, Any]] = []
        domain = self._domain()
        for user in self._users:
            for preset in _ASSIGNED[user["role"]]:
                match preset:
                    case "user_owner":
                        targets = [by_scope[("user", user["uuid"], preset)]]
                    case "domain_admin":
                        targets = [by_scope[("domain", domain["id"], preset)]]
                    case _:
                        targets = [
                            by_scope[("project", group["id"], preset)]
                            for group in self._groups
                            if user in self._accounts_in(group["id"])
                        ]
                for role in targets:
                    assigned.append({
                        "id": _identify("user_role", user["uuid"], role["id"]),
                        "user_id": user["uuid"],
                        "role_id": role["id"],
                        "granted_by": None,
                        "granted_at": _TIMESTAMP,
                    })
        return assigned

    def _permissions(self, roles: Sequence[dict[str, Any]]) -> list[dict[str, Any]]:
        rows: list[dict[str, Any]] = []
        for role in roles:
            granted = self._seeds[role["__preset"]].granted()
            for entity_type in sorted(granted):
                for bit, _ in _OPERATION_NAMES:
                    if not granted[entity_type] & bit:
                        continue
                    rows.append({
                        "id": _identify("permission", role["id"], entity_type, str(int(bit))),
                        "role_id": role["id"],
                        "entity_type": entity_type,
                        "permission": int(bit),
                    })
        return rows

    def _presets(self) -> list[dict[str, Any]]:
        return [
            {
                "id": _identify("role_preset", seed.name),
                "name": seed.name,
                "role_name_template": None,
                "scope_type": str(seed.scope_type),
                "auto_assign": seed.auto_assign,
                "deleted": False,
                "created_at": _TIMESTAMP,
                "updated_at": _TIMESTAMP,
            }
            for seed in self._seeds.values()
        ]

    def _permission_presets(self) -> list[dict[str, Any]]:
        rows: list[dict[str, Any]] = []
        for seed in self._seeds.values():
            preset_id = _identify("role_preset", seed.name)
            granted = seed.granted()
            for entity_type in sorted(granted):
                for bit, operation in _OPERATION_NAMES:
                    if not granted[entity_type] & bit:
                        continue
                    rows.append({
                        "id": _identify(
                            "role_permission_preset", preset_id, entity_type, operation
                        ),
                        "role_preset_id": preset_id,
                        "entity_type": entity_type,
                        "operation": operation,
                        "created_at": _TIMESTAMP,
                    })
        return rows

    def _role_entity(self, role: dict[str, Any]) -> str:
        return _identify("virtual_entity", "role", role["id"])

    def _virtual_entities(self, roles: Sequence[dict[str, Any]]) -> list[dict[str, Any]]:
        return [
            {"id": self._role_entity(role), "entity_type": "role", "entity_id": role["id"]}
            for role in roles
        ]

    def _entity_memberships(self, roles: Sequence[dict[str, Any]]) -> list[dict[str, Any]]:
        rows = [
            {
                "virtual_entity_id": self._role_entity(role),
                "member_entity_id": self._role_entity(role),
            }
            for role in roles
        ]
        rows.extend(
            {
                "virtual_entity_id": self._scope_entities[(role["scope_type"], role["scope_id"])],
                "member_entity_id": self._role_entity(role),
            }
            for role in roles
        )
        return rows

    def _scope_bindings(self, roles: Sequence[dict[str, Any]]) -> list[dict[str, Any]]:
        return [
            {
                "virtual_entity_id": self._role_entity(role),
                "scope_entity_id": self._role_entity(role),
            }
            for role in roles
        ]
