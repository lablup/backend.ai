from __future__ import annotations

from pathlib import Path
from typing import Any

import pytest
import yaml

# Fragments at the `public` scope and at the `default` domain of `_DOMAINS`.
_APP_CONFIG_FRAGMENTS: list[dict[str, Any]] = [
    {"config_name": "webui", "scope_type": "public", "config": {"theme": "light"}},
    {
        "config_name": "session_launcher",
        "scope_type": "domain",
        "scope_id": "0198a5a0-0000-7000-8000-00000000d001",
        "config": {"default_image": "python:3.13"},
    },
]


@pytest.fixture
def app_config_fragment_seed_dir(
    tmp_path: Path, app_config_allow_list_seed_dir: Path, domain_seed_dir: Path
) -> Path:
    """The `app_config_allow_list` and `domain` directories plus one `app_config_fragment`
    seed file, so the entries and the owning domain are written first."""
    directory = tmp_path / "app_config_fragment"
    directory.mkdir()
    (directory / "fragments.yaml").write_text(
        yaml.safe_dump({
            "kind": "app_config_fragment",
            "version": 1,
            "items": _APP_CONFIG_FRAGMENTS,
        })
    )
    return tmp_path
