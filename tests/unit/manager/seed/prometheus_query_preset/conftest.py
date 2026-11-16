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

_PROMETHEUS_QUERY_PRESETS: list[dict[str, Any]] = [
    {
        "id": "0198a5a0-0000-7000-8000-00000000f001",
        "name": "container-utilization-sum",
        "metric_name": "backendai_container_utilization",
        "query_template": "sum by (${{group_by}})(backendai_container_utilization{${{labels}}})",
        "options": {"filter_labels": ["kernel_id"], "group_labels": ["kernel_id"]},
        "description": "Instant value of the per-kernel utilization, summed",
        "rank": 100,
        "category_id": "0198a5a0-0000-7000-8000-00000000e001",
    },
    {
        "id": "0198a5a0-0000-7000-8000-00000000f002",
        "name": "vllm-request-rate",
        "metric_name": "vllm_request_success_total",
        "query_template": "sum(rate(vllm_request_success_total{${{labels}}}[${{window}}]))",
        "time_window": "5m",
        "options": {"filter_labels": [], "group_labels": []},
    },
]


@pytest.fixture
def prometheus_query_preset_seed_dir(tmp_path: Path) -> Path:
    """A directory with one `prometheus_query_preset` seed file and the
    `prometheus_query_preset_category` file its presets refer to."""
    directory = tmp_path / "prometheus_query_preset"
    directory.mkdir()
    (directory / "categories.yaml").write_text(
        yaml.safe_dump({
            "kind": "prometheus_query_preset_category",
            "version": 1,
            "items": _PROMETHEUS_QUERY_PRESET_CATEGORIES,
        })
    )
    (directory / "presets.yaml").write_text(
        yaml.safe_dump({
            "kind": "prometheus_query_preset",
            "version": 1,
            "items": _PROMETHEUS_QUERY_PRESETS,
        })
    )
    return directory
