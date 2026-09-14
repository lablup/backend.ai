from __future__ import annotations

import hashlib
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

# A derived id is a uuid7 whose timestamp is fixed and whose remaining bits come from
# what it identifies, so the same declaration writes the same file. The timestamp is
# the moment the seed was first generated.
_EPOCH_MS: Final[int] = 1757670718265
_TIMESTAMP: Final[str] = "2025-09-12 09:51:58.265582+00"
# The bits a grant is written out as, one row per bit.
_BITS: Final[tuple[Permission, ...]] = (
    Permission.READ,
    Permission.UPDATE,
    Permission.CREATE,
    Permission.SOFT_DELETE,
    Permission.HARD_DELETE,
)
# Which seed roles a user is assigned by the role their account carries. A superadmin
# bypasses the RBAC check entirely, so it holds no scope role; a monitor holds none
# either. A role its preset marks auto_assign is not listed here: every member of the
# scope holds it, which is what `auto_assign` means.
_ASSIGNED: Final[Mapping[str, tuple[str, ...]]] = {
    "superadmin": ("user_owner",),
    "admin": ("user_owner", "domain_admin", "project_admin"),
    "user": ("user_owner",),
    "monitor": ("user_owner",),
}


def _identify(*parts: str) -> str:
    """The uuid7 identifying these parts, the same on every run."""
    digest = hashlib.blake2b("|".join(parts).encode("utf-8"), digest_size=10).digest()
    value = (_EPOCH_MS & 0xFFFFFFFFFFFF) << 80 | int.from_bytes(digest, "big")
    value &= ~(0xF << 76)
    value |= 0x7 << 76
    value &= ~(0x3 << 62)
    value |= 0x2 << 62
    return str(uuid.UUID(int=value))


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
            "role_preset_id": str(self._seeds[preset].id),
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
                    "system",
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

    def _auto_assigned(self, roles: Sequence[dict[str, Any]]) -> list[dict[str, Any]]:
        """Every member of a scope holds the roles it assigns on its own."""
        assigned: list[dict[str, Any]] = []
        for role in roles:
            if not self._seeds[role["__preset"]].auto_assign:
                continue
            for user in self._accounts_in(role["scope_id"]):
                assigned.append({
                    "id": _identify("user_role", user["uuid"], role["id"]),
                    "user_id": user["uuid"],
                    "role_id": role["id"],
                    "granted_by": None,
                    "granted_at": _TIMESTAMP,
                })
        return assigned

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
        assigned.extend(self._auto_assigned(roles))
        seen = {row["id"]: row for row in assigned}
        return list(seen.values())

    def _permissions(self, roles: Sequence[dict[str, Any]]) -> list[dict[str, Any]]:
        rows: list[dict[str, Any]] = []
        for role in roles:
            granted = self._seeds[role["__preset"]].granted()
            for entity_type in sorted(granted):
                for bit in _BITS:
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
                "id": str(seed.id),
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
            preset_id = str(seed.id)
            granted = seed.granted()
            for entity_type in sorted(granted):
                for bit in _BITS:
                    if not granted[entity_type] & bit:
                        continue
                    rows.append({
                        "id": _identify(
                            "role_permission_preset", preset_id, entity_type, str(int(bit))
                        ),
                        "role_preset_id": preset_id,
                        "entity_type": entity_type,
                        "permission": int(bit),
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
