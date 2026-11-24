from __future__ import annotations

from pathlib import Path

import pytest
import yaml

_VFS_STORAGES: list[dict[str, str]] = [
    {
        "id": "0198a5a0-0000-7000-8000-00000000b001",
        "name": "local",
        "host": "local",
        "base_path": "/var/lib/backend.ai/vfs",
    },
    {
        "id": "0198a5a0-0000-7000-8000-00000000b002",
        "name": "shared",
        "host": "nfs",
        "base_path": "/mnt/vfs",
    },
]


@pytest.fixture
def vfs_storage_seed_dir(tmp_path: Path) -> Path:
    """A directory with one `vfs_storage` seed file."""
    directory = tmp_path / "vfs_storage"
    directory.mkdir()
    (directory / "storages.yaml").write_text(
        yaml.safe_dump({"kind": "vfs_storage", "version": 1, "items": _VFS_STORAGES})
    )
    return directory
