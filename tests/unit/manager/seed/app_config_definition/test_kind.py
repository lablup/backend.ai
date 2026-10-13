"""The `app_config_definition` kind reads one item per config name, and `mgr seed check`
reports what it skips."""

from __future__ import annotations

from pathlib import Path
from typing import Any

import pytest
import yaml
from click.testing import CliRunner

from ai.backend.manager.cli.seed import cli
from ai.backend.manager.errors.seed import InvalidSeedDocument
from ai.backend.manager.seed.app_config_definition.seed import AppConfigDefinitionSeed
from ai.backend.manager.seed.factory import create_seed_kind_registry
from ai.backend.manager.seed.runner import SeedPlanner


def _write(path: Path, *items: dict[str, Any]) -> Path:
    path.write_text(
        yaml.safe_dump({"kind": "app_config_definition", "version": 1, "items": list(items)})
    )
    return path


class TestAppConfigDefinitionSeed:
    def test_the_key_is_the_config_name(self) -> None:
        seed = AppConfigDefinitionSeed.model_validate({"config_name": "webui"})
        assert seed.key() == "webui"

    @pytest.mark.parametrize(
        "item",
        [
            {},
            {"config_name": ""},
            {"config_name": "x" * 129},
            {"config_name": "webui", "id": "0198a5a0-0000-7000-8000-000000000001"},
        ],
        ids=["missing", "empty", "too-long", "unknown-field"],
    )
    def test_an_invalid_item_is_refused(self, item: dict[str, Any]) -> None:
        with pytest.raises(InvalidSeedDocument):
            AppConfigDefinitionSeed.model_validate(item)


class TestAppConfigDefinitionKind:
    def test_the_files_are_planned_whole(self, app_config_definition_seed_dir: Path) -> None:
        plan = SeedPlanner(create_seed_kind_registry()).plan([app_config_definition_seed_dir])
        assert plan.rejections == []
        [batch] = plan.batches
        assert batch.kind.name == "app_config_definition"
        assert [item.key() for item in batch.items()] == ["webui", "session_launcher"]

    def test_a_name_stated_in_two_files_skips_both(self, tmp_path: Path) -> None:
        first = _write(tmp_path / "first.yaml", {"config_name": "webui"})
        second = _write(tmp_path / "second.yaml", {"config_name": "webui"})
        plan = SeedPlanner(create_seed_kind_registry()).plan([first, second])
        assert sorted(rejection.source for rejection in plan.rejections) == [
            str(first),
            str(second),
        ]
        assert plan.batches == []


class TestCheckCommand:
    def test_the_files_pass(self, app_config_definition_seed_dir: Path) -> None:
        result = CliRunner().invoke(cli, ["check", str(app_config_definition_seed_dir)])
        assert result.exit_code == 0, result.output
        assert "app_config_definition: 1 files, 2 items" in result.output

    def test_an_invalid_item_fails_the_command(self, tmp_path: Path) -> None:
        path = _write(tmp_path / "bad.yaml", {"config_name": ""})
        result = CliRunner().invoke(cli, ["check", str(path)])
        assert result.exit_code != 0
