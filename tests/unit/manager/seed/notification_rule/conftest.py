from __future__ import annotations

from pathlib import Path
from typing import Any

import pytest
import yaml

_NOTIFICATION_RULES: list[dict[str, Any]] = [
    {
        "id": "0198a5a0-0000-7000-8000-00000000d001",
        "name": "session-started",
        "rule_type": "session.started",
        "channel_id": "0198a5a0-0000-7000-8000-00000000c001",
        "message_template": "Session {{ session_id }} started",
        "created_by": "f38dea23-50fa-42a0-b5ae-338f5f4693f4",
    },
    {
        "id": "0198a5a0-0000-7000-8000-00000000d002",
        "name": "artifact-downloaded",
        "description": "Mail when a download completes",
        "rule_type": "artifact.download.completed",
        "channel_id": "0198a5a0-0000-7000-8000-00000000c002",
        "message_template": "Artifact {{ artifact_id }} downloaded",
        "enabled": False,
        "created_by": "f38dea23-50fa-42a0-b5ae-338f5f4693f4",
    },
]


@pytest.fixture
def notification_rule_seed_dir(tmp_path: Path) -> Path:
    """A directory with one `notification_rule` seed file."""
    directory = tmp_path / "notification_rule"
    directory.mkdir()
    (directory / "rules.yaml").write_text(
        yaml.safe_dump({
            "kind": "notification_rule",
            "version": 1,
            "items": _NOTIFICATION_RULES,
        })
    )
    return directory
