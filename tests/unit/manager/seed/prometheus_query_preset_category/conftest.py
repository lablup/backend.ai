from __future__ import annotations

from pathlib import Path
from typing import Any

import pytest
import yaml

_PROMETHEUS_QUERY_PRESET_CATEGORIES: list[dict[str, Any]] = [
    {
        "id": "0198a5a0-0000-7000-8000-00000000e001",
        "name": "container",
        "description": "Container-level utilization metrics",
    },
    {"id": "0198a5a0-0000-7000-8000-00000000e002", "name": "vllm-inference"},
]


@pytest.fixture
def prometheus_query_preset_category_seed_dir(tmp_path: Path) -> Path:
    """A directory with one `prometheus_query_preset_category` seed file."""
    directory = tmp_path / "prometheus_query_preset_category"
    directory.mkdir()
    (directory / "categories.yaml").write_text(
        yaml.safe_dump({
            "kind": "prometheus_query_preset_category",
            "version": 1,
            "items": _PROMETHEUS_QUERY_PRESET_CATEGORIES,
        })
    )
    return directory
