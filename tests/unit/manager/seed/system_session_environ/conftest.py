from __future__ import annotations

from pathlib import Path
from typing import Any

import pytest
import yaml

# Bindings at the `public` scope and at the `default` domain of `_DOMAINS`.
_SYSTEM_SESSION_ENVIRONS: list[dict[str, Any]] = [
    {
        "value_source": "session_id",
        "key": "BACKENDAI_SESSION_ID",
        "scope_type": "public",
    },
    {
        "value_source": "user_email",
        "key": "BACKENDAI_USER_EMAIL",
        "scope_type": "domain",
        "scope_id": "0198a5a0-0000-7000-8000-00000000d001",
    },
]


@pytest.fixture
def system_session_environ_seed_dir(tmp_path: Path, domain_seed_dir: Path) -> Path:
    """The `domain` directory plus one `system_session_environ` seed file, so the owning
    domain is written first."""
    directory = tmp_path / "system_session_environ"
    directory.mkdir()
    (directory / "bindings.yaml").write_text(
        yaml.safe_dump({
            "kind": "system_session_environ",
            "version": 1,
            "items": _SYSTEM_SESSION_ENVIRONS,
        })
    )
    return tmp_path
