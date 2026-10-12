"""The `prometheus_query_preset` kind reads one item per preset id, and `mgr seed check`
reports what it skips."""

from __future__ import annotations

from pathlib import Path
from typing import Any

import pytest
import yaml
from click.testing import CliRunner

from ai.backend.manager.cli.seed import cli
from ai.backend.manager.errors.seed import InvalidSeedDocument
from ai.backend.manager.seed.factory import create_seed_kind_registry
from ai.backend.manager.seed.prometheus_query_preset.seed import PrometheusQueryPresetSeed
from ai.backend.manager.seed.runner import SeedPlanner

_ID = "0198a5a0-0000-7000-8000-00000000f001"
_ITEM: dict[str, Any] = {
    "id": _ID,
    "name": "container-utilization-sum",
    "metric_name": "backendai_container_utilization",
    "query_template": "sum(backendai_container_utilization)",
    "options": {"filter_labels": [], "group_labels": []},
}


def _write(path: Path, *items: dict[str, Any]) -> Path:
    path.write_text(
        yaml.safe_dump({"kind": "prometheus_query_preset", "version": 1, "items": list(items)})
    )
    return path


class TestPrometheusQueryPresetSeed:
    def test_the_key_is_the_id(self) -> None:
        seed = PrometheusQueryPresetSeed.model_validate(_ITEM)
        assert seed.key() == _ID
        assert seed.time_window is None
        assert seed.description is None
        assert seed.rank == 0
        assert seed.category_id is None

    @pytest.mark.parametrize(
        "change",
        [
            {"id": None},
            {"id": "not-a-uuid"},
            {"name": ""},
            {"name": "x" * 257},
            {"metric_name": "x" * 257},
            {"query_template": ""},
            {"time_window": "x" * 33},
            {"options": None},
            {"options": {"filter_labels": []}},
            {"rank": 2**31},
            {"category_id": "not-a-uuid"},
            {"category_name": "container"},
        ],
        ids=[
            "missing-id",
            "invalid-id",
            "empty-name",
            "too-long-name",
            "too-long-metric-name",
            "empty-query-template",
            "too-long-time-window",
            "missing-options",
            "incomplete-options",
            "rank-out-of-range",
            "invalid-category-id",
            "unknown",
        ],
    )
    def test_an_invalid_item_is_refused(self, change: dict[str, Any]) -> None:
        item = {**_ITEM, **change}
        item = {key: value for key, value in item.items() if value is not None}
        with pytest.raises(InvalidSeedDocument):
            PrometheusQueryPresetSeed.model_validate(item)


class TestPrometheusQueryPresetKind:
    def test_the_files_are_planned_after_the_categories(
        self, prometheus_query_preset_seed_dir: Path
    ) -> None:
        plan = SeedPlanner(create_seed_kind_registry()).plan([prometheus_query_preset_seed_dir])
        assert plan.rejections == []
        assert [batch.kind.name for batch in plan.batches] == [
            "prometheus_query_preset_category",
            "prometheus_query_preset",
        ]
        assert [item.key() for item in plan.batches[1].items()] == [
            "0198a5a0-0000-7000-8000-00000000f001",
            "0198a5a0-0000-7000-8000-00000000f002",
        ]

    def test_an_id_stated_in_two_files_skips_both(self, tmp_path: Path) -> None:
        first = _write(tmp_path / "first.yaml", _ITEM)
        second = _write(tmp_path / "second.yaml", {**_ITEM, "name": "other"})
        plan = SeedPlanner(create_seed_kind_registry()).plan([first, second])
        assert sorted(rejection.source for rejection in plan.rejections) == [
            str(first),
            str(second),
        ]
        assert plan.batches == []


class TestCheckCommand:
    def test_the_files_pass(self, prometheus_query_preset_seed_dir: Path) -> None:
        result = CliRunner().invoke(cli, ["check", str(prometheus_query_preset_seed_dir)])
        assert result.exit_code == 0, result.output
        assert "prometheus_query_preset: 1 files, 2 items" in result.output

    def test_an_invalid_item_fails_the_command(self, tmp_path: Path) -> None:
        path = _write(tmp_path / "bad.yaml", {**_ITEM, "name": ""})
        result = CliRunner().invoke(cli, ["check", str(path)])
        assert result.exit_code != 0
