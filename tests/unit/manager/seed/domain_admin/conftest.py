from __future__ import annotations

from pathlib import Path
from typing import Any

import pytest
import yaml

from ai.backend.manager.seed.role_preset.kinds import PermissionKinds

# Domain seed files written for the tests, one domain per file.
_DOMAINS: dict[str, dict[str, Any]] = {
    "default.yaml": {
        "id": "0198a5a0-0000-7000-8000-00000000d001",
        "name": "default",
        "description": "The default domain",
        "is_default": True,
        "total_resource_slots": {"cpu": "8", "mem": "17179869184"},
        "allowed_vfolder_hosts": {"local:volume1": ["create-vfolder", "mount-in-session"]},
        "allowed_docker_registries": ["cr.backend.ai"],
    },
    "research.yaml": {
        "id": "0198a5a0-0000-7000-8000-00000000d002",
        "name": "research",
    },
}

# User seed files written for the tests, one user per file, in the `default` domain under
# the `default` resource policies. `admin` states every field but `allowed_client_ip`, and two keypairs; `member`
# leaves the optional ones to their defaults.
_USERS: dict[str, dict[str, Any]] = {
    "admin.yaml": {
        "id": "0198a5a0-0000-7000-8000-00000000f001",
        "domain_id": "0198a5a0-0000-7000-8000-00000000d001",
        "email": "admin@example.com",
        "username": "admin",
        "password": "admin-password",
        "need_password_change": True,
        "full_name": "Admin",
        "description": "The administrator",
        "status": "active",
        "status_info": "seeded",
        "role": "superadmin",
        "resource_policy_id": "0198a5a0-0000-7000-8000-00000000b001",
        "sudo_session_enabled": True,
        "container_uid": 1000,
        "container_main_gid": 1000,
        "container_gids": [1000, 1001],
        "keypairs": [
            {
                "access_key": "AKIAADMINDEFAULT0001",
                "secret_key": "admin-default-secret",
                "is_admin": True,
                "is_default": True,
                "resource_policy_id": "0198a5a0-0000-7000-8000-00000000b003",
                "rate_limit": 30000,
            },
            {
                "access_key": "AKIAADMINSECOND00002",
                "secret_key": "admin-second-secret",
                "is_active": False,
                "resource_policy_id": "0198a5a0-0000-7000-8000-00000000b003",
            },
        ],
    },
    "member.yaml": {
        "id": "0198a5a0-0000-7000-8000-00000000f002",
        "domain_id": "0198a5a0-0000-7000-8000-00000000d001",
        "email": "member@example.com",
        "username": "member",
        "password": "member-password",
        "resource_policy_id": "0198a5a0-0000-7000-8000-00000000b001",
    },
}

_ALL: list[str] = ["read", "update", "create", "soft_delete", "hard_delete"]
# Role files written for the tests, one role per file. The admin states `agent: [read]` and
# leaves `app_config` empty; every role states every entity type, as a role file must.
_ROLES: dict[str, dict[str, Any]] = {
    "domain-admin.yaml": {
        "id": "0198a5a0-0000-7000-8000-00000000a001",
        "name": "domain_admin",
        "scope_type": "domain",
        "auto_assign": False,
        "permissions": {"agent": ["read"], "domain": ["read", "update"], "project": _ALL},
    },
    "domain-member.yaml": {
        "id": "0198a5a0-0000-7000-8000-00000000a002",
        "name": "domain_member",
        "scope_type": "domain",
        "auto_assign": True,
        "permissions": {"domain": ["read"], "project": ["read"]},
    },
    "public-member.yaml": {
        "id": "0198a5a0-0000-7000-8000-00000000a003",
        "name": "public_member",
        "scope_type": "global",
        "scope": "public",
        "auto_assign": True,
        "permissions": {"image": ["read"]},
    },
}

# Domain admin items written for the tests: `member` granted the `domain_admin` role of
# the `default` domain.
_DOMAIN_ADMINS: list[dict[str, str]] = [
    {"domain_id": _DOMAINS["default.yaml"]["id"], "user_id": _USERS["member.yaml"]["id"]},
]

# The role of the `domain_admin` preset in the `default` domain.
_DOMAIN_ADMIN_ROLE_ID = "0198a5a0-0000-7000-8000-000000001401"


@pytest.fixture
def domain_admin_role_id() -> str:
    return _DOMAIN_ADMIN_ROLE_ID


@pytest.fixture
def domain_admin_seed_dir(role_kind_seed_dir: Path) -> Path:
    """The role directory plus the `domain_admin` preset, the role made from it in the
    `default` domain, and one domain_admin file, so the role the items name is written
    first."""
    preset = _preset_item(_ROLES["domain-admin.yaml"])
    (role_kind_seed_dir / "preset-domain-admin.yaml").write_text(
        yaml.safe_dump({"kind": "role_preset", "version": 1, "items": [preset]})
    )
    domain_id = _DOMAINS["default.yaml"]["id"]
    (role_kind_seed_dir / "role-domain-admin.yaml").write_text(
        yaml.safe_dump({
            "kind": "role",
            "version": 1,
            "items": [
                {
                    "id": _DOMAIN_ADMIN_ROLE_ID,
                    "name": f"domain_admin-{domain_id[:8]}",
                    "scope_type": "domain",
                    "scope_id": domain_id,
                    "role_preset_id": preset["id"],
                }
            ],
        })
    )
    (role_kind_seed_dir / "domain-admins.yaml").write_text(
        yaml.safe_dump({"kind": "domain_admin", "version": 1, "items": _DOMAIN_ADMINS})
    )
    return role_kind_seed_dir


def _preset_item(role: dict[str, Any]) -> dict[str, Any]:
    """A role file's item with every entity type stated, as a role file must."""
    permissions = {kind: [] for kind in PermissionKinds().declared()} | role["permissions"]
    return role | {"permissions": permissions}
