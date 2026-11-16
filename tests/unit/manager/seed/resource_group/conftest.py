from __future__ import annotations

from pathlib import Path
from typing import Any

import pytest
import yaml

# Resource group seed file written for the tests. `default` states every field; `gpu`
# leaves the optional ones to their defaults.
_RESOURCE_GROUPS: list[dict[str, Any]] = [
    {
        "id": "0198a5a0-0000-7000-8000-00000000e001",
        "name": "default",
        "description": "The default resource group",
        "is_default": True,
        "wsproxy_addr": "http://127.0.0.1:5050",
        "wsproxy_api_token": "token",
        "driver": "static",
        "driver_opts": {"x": 1},
        "scheduler": "fifo",
        "scheduler_opts": {"pending_timeout": 30},
        "use_host_network": True,
    },
    {
        "id": "0198a5a0-0000-7000-8000-00000000e002",
        "name": "gpu",
        "driver": "static",
        "scheduler": "fifo",
    },
]


@pytest.fixture
def resource_group_seed_dir(tmp_path: Path) -> Path:
    """A directory with one `resource_group` seed file."""
    directory = tmp_path / "resource_group"
    directory.mkdir()
    (directory / "resource-groups.yaml").write_text(
        yaml.safe_dump({"kind": "resource_group", "version": 1, "items": _RESOURCE_GROUPS})
    )
    return directory


@pytest.fixture
def default_resource_group_id() -> str:
    return str(_RESOURCE_GROUPS[0]["id"])
