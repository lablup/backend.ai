from __future__ import annotations

from pathlib import Path
from typing import Any

import pytest
import yaml

_IDLE_CHECKERS: list[dict[str, Any]] = [
    {
        "id": "0198a5a0-0000-7000-8000-00000000f001",
        "name": "session-lifetime",
        "description": "Terminates sessions running longer than a day.",
        "target_session_types": ["interactive", "batch"],
        "spec": {"type": "session_lifetime", "session_lifetime": {"max_lifetime_seconds": 86400}},
    },
    {
        "id": "0198a5a0-0000-7000-8000-00000000f002",
        "name": "network-timeout",
        "target_session_types": ["interactive"],
        "initial_grace_period_seconds": 300,
        "spec": {
            "type": "network_timeout",
            "network": {"max_network_inactivity_seconds": 3600},
        },
    },
]

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


@pytest.fixture
def idle_checker_assignment_seed_dir(
    tmp_path: Path, idle_checker_seed_dir: Path, domain_seed_dir: Path
) -> Path:
    """The `idle_checker` and `domain` directories plus one `idle_checker_assignment` seed
    file applying every checker to the default domain."""
    directory = tmp_path / "idle_checker_assignment"
    directory.mkdir()
    domain_id = _DOMAINS["default.yaml"]["id"]
    items = [
        {"idle_checker_id": checker["id"], "scope_type": "domain", "scope_id": domain_id}
        for checker in _IDLE_CHECKERS
    ]
    (directory / "assignments.yaml").write_text(
        yaml.safe_dump({"kind": "idle_checker_assignment", "version": 1, "items": items})
    )
    return tmp_path
