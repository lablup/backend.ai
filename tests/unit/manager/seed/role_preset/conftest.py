from __future__ import annotations

from pathlib import Path
from typing import Any

import pytest
import yaml

from ai.backend.manager.seed.role_preset.kinds import PermissionKinds

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


@pytest.fixture
def role_seed_dir(tmp_path: Path) -> Path:
    """A directory of role seed files, the shape `seeds/manager/role_preset/` has."""
    directory = tmp_path / "role_preset"
    directory.mkdir()
    for file_name, role in _ROLES.items():
        (directory / file_name).write_text(
            yaml.safe_dump({"kind": "role_preset", "version": 1, "items": [_preset_item(role)]})
        )
    return directory


@pytest.fixture
def domain_admin_id() -> str:
    return str(_ROLES["domain-admin.yaml"]["id"])


def _preset_item(role: dict[str, Any]) -> dict[str, Any]:
    """A role file's item with every entity type stated, as a role file must."""
    permissions = {kind: [] for kind in PermissionKinds().declared()} | role["permissions"]
    return role | {"permissions": permissions}
