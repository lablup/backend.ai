from __future__ import annotations

from pathlib import Path

import pytest
import yaml

_STORAGE_BACKEND_TYPES: dict[str, list[str]] = {
    "vfs": ["vfolder", "metric", "fast-fs-size"],
    "noop": [],
}


@pytest.fixture
def storage_backend_type_seed_dir(tmp_path: Path) -> Path:
    """A directory with one `storage_backend_type` seed file."""
    directory = tmp_path / "storage_backend_type"
    directory.mkdir()
    items = [
        {"name": name, "capabilities": capabilities}
        for name, capabilities in _STORAGE_BACKEND_TYPES.items()
    ]
    (directory / "types.yaml").write_text(
        yaml.safe_dump({"kind": "storage_backend_type", "version": 1, "items": items})
    )
    return directory
