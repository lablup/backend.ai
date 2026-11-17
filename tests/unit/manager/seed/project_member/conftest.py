from __future__ import annotations

from pathlib import Path
from typing import Any

import pytest
import yaml

# Project seed files written for the tests, one project per file, in the `default` domain
# under the `default` project resource policy.
_PROJECTS: dict[str, dict[str, Any]] = {
    "research.yaml": {
        "id": "0198a5a0-0000-7000-8000-00000000e001",
        "domain_id": "0198a5a0-0000-7000-8000-00000000d001",
        "name": "research",
        "resource_policy_id": "0198a5a0-0000-7000-8000-00000000b002",
        "description": "Research project",
        "total_resource_slots": {"cpu": "4"},
        "allowed_vfolder_hosts": {"local:volume1": ["create-vfolder", "mount-in-session"]},
    },
    "model-store.yaml": {
        "id": "0198a5a0-0000-7000-8000-00000000e002",
        "domain_id": "0198a5a0-0000-7000-8000-00000000d001",
        "name": "model-store",
        "type": "model-store",
        "resource_policy_id": "0198a5a0-0000-7000-8000-00000000b002",
        "description": "Model Store",
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

# Project member items written for the tests: `admin` on `research`, `member` on
# `model-store`.
_PROJECT_MEMBERS: list[dict[str, str]] = [
    {"project_id": _PROJECTS["research.yaml"]["id"], "user_id": _USERS["admin.yaml"]["id"]},
    {"project_id": _PROJECTS["model-store.yaml"]["id"], "user_id": _USERS["member.yaml"]["id"]},
]


@pytest.fixture
def project_member_seed_dir(role_kind_seed_dir: Path) -> Path:
    """The role directory plus a project member file, so the projects, the users and the
    auto_assign role the items name are written first."""
    (role_kind_seed_dir / "project-members.yaml").write_text(
        yaml.safe_dump({"kind": "project_member", "version": 1, "items": _PROJECT_MEMBERS})
    )
    return role_kind_seed_dir
