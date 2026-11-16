from __future__ import annotations

from pathlib import Path
from typing import Any

import pytest
import yaml

# One global Harbor registry and one registry reachable only from the projects bound to it.
_CONTAINER_REGISTRIES: list[dict[str, Any]] = [
    {
        "id": "0198a5a0-0000-7000-8000-00000000c001",
        "registry_name": "cr.backend.ai",
        "url": "https://cr.backend.ai",
        "type": "harbor2",
        "project": "stable",
    },
    {
        "id": "0198a5a0-0000-7000-8000-00000000c002",
        "registry_name": "local",
        "url": "http://localhost",
        "type": "local",
        "project": "stable",
        "is_global": False,
        "username": "admin",
        "password": "secret",
        "ssl_verify": False,
        "extra": {"note": "seed"},
    },
]

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


@pytest.fixture
def container_registry_project_seed_dir(project_seed_dir: Path) -> Path:
    """The project directory plus the registries and the projects allowed on them, the
    research project taking the first registry as its default."""
    (project_seed_dir / "registries.yaml").write_text(
        yaml.safe_dump({"kind": "container_registry", "version": 1, "items": _CONTAINER_REGISTRIES})
    )
    research = _PROJECTS["research.yaml"]["id"]
    allowed = [
        {"registry_id": _CONTAINER_REGISTRIES[0]["id"], "project_id": research, "is_default": True},
        {"registry_id": _CONTAINER_REGISTRIES[1]["id"], "project_id": research},
    ]
    (project_seed_dir / "allowed-registries.yaml").write_text(
        yaml.safe_dump({"kind": "container_registry_project", "version": 1, "items": allowed})
    )
    return project_seed_dir
