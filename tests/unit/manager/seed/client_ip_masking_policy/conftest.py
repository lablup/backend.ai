from __future__ import annotations

from pathlib import Path
from typing import Any

import pytest
import yaml

_CLIENT_IP_MASKING_POLICIES: list[dict[str, Any]] = [
    {"target_type": "default", "mode": "truncate", "ipv4_prefix": 24, "ipv6_prefix": 48},
    {"target_type": "audit_logs", "mode": "drop"},
]


@pytest.fixture
def client_ip_masking_policy_seed_dir(tmp_path: Path) -> Path:
    """A directory with one `client_ip_masking_policy` seed file."""
    directory = tmp_path / "client_ip_masking_policy"
    directory.mkdir()
    (directory / "policies.yaml").write_text(
        yaml.safe_dump({
            "kind": "client_ip_masking_policy",
            "version": 1,
            "items": _CLIENT_IP_MASKING_POLICIES,
        })
    )
    return directory
