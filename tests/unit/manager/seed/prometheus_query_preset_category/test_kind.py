"""The `prometheus_query_preset_category` kind reads one item per category id, and
`mgr seed check` reports what it skips."""

from __future__ import annotations

from pathlib import Path
from typing import Any

import pytest
import yaml
from click.testing import CliRunner

from ai.backend.manager.cli.seed import cli
from ai.backend.manager.errors.seed import InvalidSeedDocument
from ai.backend.manager.seed.factory import create_seed_kind_registry
from ai.backend.manager.seed.prometheus_query_preset_category.seed import (
    PrometheusQueryPresetCategorySeed,
)
from ai.backend.manager.seed.runner import SeedPlanner

_ID = "0198a5a0-0000-7000-8000-00000000e001"


def _write(path: Path, *items: dict[str, Any]) -> Path:
    path.write_text(
        yaml.safe_dump({
            "kind": "prometheus_query_preset_category",
            "version": 1,
            "items": list(items),
        })
    )
    return path


class TestPrometheusQueryPresetCategorySeed:
    def test_the_key_is_the_id(self) -> None:
        seed = PrometheusQueryPresetCategorySeed.model_validate({"id": _ID, "name": "container"})
        assert seed.key() == _ID
        assert seed.description is None

    @pytest.mark.parametrize(
        "item",
        [
            {"name": "container"},
            {"id": "not-a-uuid", "name": "container"},
            {"id": _ID},
            {"id": _ID, "name": ""},
            {"id": _ID, "name": "x" * 129},
            {"id": _ID, "name": "container", "rank": 1},
        ],
        ids=["missing-id", "invalid-id", "missing-name", "empty-name", "too-long-name", "unknown"],
    )
    def test_an_invalid_item_is_refused(self, item: dict[str, Any]) -> None:
        with pytest.raises(InvalidSeedDocument):
            PrometheusQueryPresetCategorySeed.model_validate(item)


class TestPrometheusQueryPresetCategoryKind:
    def test_the_files_are_planned_whole(
        self, prometheus_query_preset_category_seed_dir: Path
    ) -> None:
        plan = SeedPlanner(create_seed_kind_registry()).plan([
            prometheus_query_preset_category_seed_dir
        ])
        assert plan.rejections == []
        [batch] = plan.batches
        assert batch.kind.name == "prometheus_query_preset_category"
        assert [item.key() for item in batch.items()] == [
            "0198a5a0-0000-7000-8000-00000000e001",
            "0198a5a0-0000-7000-8000-00000000e002",
        ]

    def test_an_id_stated_in_two_files_skips_both(self, tmp_path: Path) -> None:
        first = _write(tmp_path / "first.yaml", {"id": _ID, "name": "container"})
        second = _write(tmp_path / "second.yaml", {"id": _ID, "name": "gpu"})
        plan = SeedPlanner(create_seed_kind_registry()).plan([first, second])
        assert sorted(rejection.source for rejection in plan.rejections) == [
            str(first),
            str(second),
        ]
        assert plan.batches == []


class TestCheckCommand:
    def test_the_files_pass(self, prometheus_query_preset_category_seed_dir: Path) -> None:
        result = CliRunner().invoke(cli, ["check", str(prometheus_query_preset_category_seed_dir)])
        assert result.exit_code == 0, result.output
        assert "prometheus_query_preset_category: 1 files, 2 items" in result.output

    def test_an_invalid_item_fails_the_command(self, tmp_path: Path) -> None:
        path = _write(tmp_path / "bad.yaml", {"id": _ID, "name": ""})
        result = CliRunner().invoke(cli, ["check", str(path)])
        assert result.exit_code != 0


class TestPrometheusQueryPresetCategorySeedCheck:
    def test_an_item_keeping_the_rules_passes(self) -> None:
        assert (
            PrometheusQueryPresetCategorySeed.model_validate({
                "id": _ID,
                "name": "container",
            }).check()
            == []
        )

    @pytest.mark.parametrize(
        "item",
        [
            {"id": _ID, "name": "  "},
        ],
        ids=[
            "blank-name",
        ],
    )
    def test_an_item_breaking_a_rule_fails(self, item: dict[str, Any]) -> None:
        assert len(PrometheusQueryPresetCategorySeed.model_validate(item).check()) == 1
