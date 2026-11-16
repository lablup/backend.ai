from __future__ import annotations

from pathlib import Path
from typing import Any

import pytest
import yaml

_NOTIFICATION_CHANNELS: list[dict[str, Any]] = [
    {
        "id": "0198a5a0-0000-7000-8000-00000000c001",
        "name": "ops-webhook",
        "channel_type": "webhook",
        "spec": {"url": "https://hooks.example.com/ops"},
        "created_by": "f38dea23-50fa-42a0-b5ae-338f5f4693f4",
    },
    {
        "id": "0198a5a0-0000-7000-8000-00000000c002",
        "name": "ops-email",
        "description": "Mail to the operators",
        "channel_type": "email",
        "spec": {
            "smtp": {"host": "smtp.example.com", "port": 587},
            "message": {"from_email": "noreply@example.com", "to_emails": ["ops@example.com"]},
        },
        "enabled": False,
        "created_by": "f38dea23-50fa-42a0-b5ae-338f5f4693f4",
    },
]


@pytest.fixture
def notification_channel_seed_dir(tmp_path: Path) -> Path:
    """A directory with one `notification_channel` seed file."""
    directory = tmp_path / "notification_channel"
    directory.mkdir()
    (directory / "channels.yaml").write_text(
        yaml.safe_dump({
            "kind": "notification_channel",
            "version": 1,
            "items": _NOTIFICATION_CHANNELS,
        })
    )
    return directory
