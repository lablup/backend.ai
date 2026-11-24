from __future__ import annotations

from pathlib import Path
from typing import Any

import pytest
import yaml

_RETENTION_POLICIES: list[dict[str, Any]] = [
    {
        "id": "0198a5a0-0000-7000-8000-00000000d001",
        "category": "logs",
        "retention_period_days": 365,
        "enabled": False,
    },
    {
        "id": "0198a5a0-0000-7000-8000-00000000d002",
        "category": "usage_records",
        "retention_period_days": 90,
        "enabled": True,
    },
]


@pytest.fixture
def retention_policy_seed_dir(tmp_path: Path) -> Path:
    """A directory with one `retention_policy` seed file."""
    directory = tmp_path / "retention_policy"
    directory.mkdir()
    (directory / "policies.yaml").write_text(
        yaml.safe_dump({"kind": "retention_policy", "version": 1, "items": _RETENTION_POLICIES})
    )
    return directory
