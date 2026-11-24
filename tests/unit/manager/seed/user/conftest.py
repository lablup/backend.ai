from __future__ import annotations

from pathlib import Path
from typing import Any

import pytest
import yaml

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

# Resource policy files written for the tests, one kind per file.
_RESOURCE_POLICIES: dict[str, dict[str, Any]] = {
    "user_resource_policy": {
        "uuid": "0198a5a0-0000-7000-8000-00000000b001",
        "name": "default",
        "max_vfolder_count": 0,
        "max_quota_scope_size": -1,
        "max_session_count_per_model_session": 10,
    },
    "project_resource_policy": {
        "uuid": "0198a5a0-0000-7000-8000-00000000b002",
        "name": "default",
        "max_vfolder_count": 0,
        "max_quota_scope_size": -1,
        "max_network_count": 3,
    },
    "keypair_resource_policy": {
        "uuid": "0198a5a0-0000-7000-8000-00000000b003",
        "name": "default",
        "is_default": True,
        "total_resource_slots": {"cpu": "4", "mem": "8589934592"},
        "max_concurrent_sessions": 5,
        "max_containers_per_session": 1,
        "idle_timeout": 3600,
        "max_pending_session_resource_slots": {"cpu": "2"},
        "allowed_vfolder_hosts": {"local:volume1": ["mount-in-session", "create-vfolder"]},
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


@pytest.fixture
def user_seed_dir(tmp_path: Path) -> Path:
    """A directory of user seed files with the domains and the resource policies they
    refer to."""
    directory = tmp_path / "user"
    directory.mkdir()
    for file_name, domain in _DOMAINS.items():
        (directory / f"domain-{file_name}").write_text(
            yaml.safe_dump({"kind": "domain", "version": 1, "items": [domain]})
        )
    for kind in ("user_resource_policy", "keypair_resource_policy"):
        (directory / f"{kind}.yaml").write_text(
            yaml.safe_dump({"kind": kind, "version": 1, "items": [_RESOURCE_POLICIES[kind]]})
        )
    for file_name, user in _USERS.items():
        (directory / file_name).write_text(
            yaml.safe_dump({"kind": "user", "version": 1, "items": [user]})
        )
    return directory
