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


@pytest.fixture
def container_registry_seed_dir(tmp_path: Path) -> Path:
    """A directory with one `container_registry` seed file."""
    directory = tmp_path / "container_registry"
    directory.mkdir()
    (directory / "registries.yaml").write_text(
        yaml.safe_dump({"kind": "container_registry", "version": 1, "items": _CONTAINER_REGISTRIES})
    )
    return directory
