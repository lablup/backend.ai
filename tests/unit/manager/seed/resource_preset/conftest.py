from __future__ import annotations

from pathlib import Path
from typing import Any

import pytest
import yaml

# Resource preset files written for the tests, one preset per file, both bound to no
# resource group. `small` states every field; `large` leaves `shared_memory` out.
_RESOURCE_PRESETS: dict[str, dict[str, Any]] = {
    "small.yaml": {
        "id": "0198a5a0-0000-7000-8000-000000001001",
        "name": "small",
        "resource_slots": {"cpu": "1", "mem": "1073741824"},
        "shared_memory": "64m",
    },
    "large.yaml": {
        "id": "0198a5a0-0000-7000-8000-000000001002",
        "name": "large",
        "resource_slots": {"cpu": "8", "mem": "17179869184", "cuda.shares": "1"},
    },
}


@pytest.fixture
def resource_preset_seed_dir(tmp_path: Path) -> Path:
    """A directory of resource preset seed files, the shape `seeds/manager/resource_preset/`
    has."""
    directory = tmp_path / "resource_preset"
    directory.mkdir()
    for file_name, preset in _RESOURCE_PRESETS.items():
        (directory / file_name).write_text(
            yaml.safe_dump({"kind": "resource_preset", "version": 1, "items": [preset]})
        )
    return directory


@pytest.fixture
def small_preset_id() -> str:
    return str(_RESOURCE_PRESETS["small.yaml"]["id"])
