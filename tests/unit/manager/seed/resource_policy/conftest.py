from __future__ import annotations

from pathlib import Path
from typing import Any

import pytest
import yaml

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


@pytest.fixture
def resource_policy_seed_dir(tmp_path: Path) -> Path:
    """A directory of resource policy seed files, one file per kind."""
    directory = tmp_path / "resource_policy"
    directory.mkdir()
    for kind, item in _RESOURCE_POLICIES.items():
        (directory / f"{kind}.yaml").write_text(
            yaml.safe_dump({"kind": kind, "version": 1, "items": [item]})
        )
    return directory
