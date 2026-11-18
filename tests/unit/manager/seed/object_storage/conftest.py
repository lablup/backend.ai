from __future__ import annotations

from pathlib import Path
from typing import Any

import pytest
import yaml

_OBJECT_STORAGES: list[dict[str, Any]] = [
    {
        "id": "0198a5a0-0000-7000-8000-00000000b001",
        "name": "minio",
        "host": "storage-proxy",
        "access_key": "minioadmin",
        "secret_key": "minioadmin",
        "endpoint": "http://127.0.0.1:9000",
        "region": "us-east-1",
    },
    {
        "id": "0198a5a0-0000-7000-8000-00000000b002",
        "name": "archive",
        "host": "storage-proxy",
        "access_key": "archive-key",
        "secret_key": "archive-secret",
        "endpoint": "http://127.0.0.1:9001",
    },
]


@pytest.fixture
def object_storage_seed_dir(tmp_path: Path) -> Path:
    """A directory with one `object_storage` seed file."""
    directory = tmp_path / "object_storage"
    directory.mkdir()
    (directory / "storages.yaml").write_text(
        yaml.safe_dump({"kind": "object_storage", "version": 1, "items": _OBJECT_STORAGES})
    )
    return directory
