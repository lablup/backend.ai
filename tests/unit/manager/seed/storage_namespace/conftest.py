from __future__ import annotations

from pathlib import Path

import pytest
import yaml

_STORAGE_NAMESPACES: list[dict[str, str]] = [
    {
        "id": "0198a5a0-0000-7000-8000-00000000c001",
        "storage_id": "0198a5a0-0000-7000-8000-00000000b001",
        "namespace": "artifacts",
    },
    {
        "id": "0198a5a0-0000-7000-8000-00000000c002",
        "storage_id": "0198a5a0-0000-7000-8000-00000000b002",
        "namespace": "archive",
    },
]


@pytest.fixture
def storage_namespace_seed_dir(tmp_path: Path) -> Path:
    """A directory with one `storage_namespace` seed file."""
    directory = tmp_path / "storage_namespace"
    directory.mkdir()
    (directory / "namespaces.yaml").write_text(
        yaml.safe_dump({"kind": "storage_namespace", "version": 1, "items": _STORAGE_NAMESPACES})
    )
    return directory
