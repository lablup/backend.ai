from __future__ import annotations

from pathlib import Path
from typing import Any

import pytest
import yaml

_LOGIN_CLIENT_TYPES: list[dict[str, Any]] = [
    {"id": "0198a5a0-0000-7000-8000-00000000c001", "name": "webui", "description": "Web UI"},
    {"id": "0198a5a0-0000-7000-8000-00000000c002", "name": "cli"},
]


@pytest.fixture
def login_client_type_seed_dir(tmp_path: Path) -> Path:
    """A directory with one `login_client_type` seed file."""
    directory = tmp_path / "login_client_type"
    directory.mkdir()
    (directory / "types.yaml").write_text(
        yaml.safe_dump({"kind": "login_client_type", "version": 1, "items": _LOGIN_CLIENT_TYPES})
    )
    return directory
