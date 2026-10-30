"""The `app_config_allow_list` kind reads one item per config name and scope type, and
`mgr seed check` reports what it skips."""

from __future__ import annotations

from pathlib import Path
from typing import Any

import pytest
import yaml
from click.testing import CliRunner

from ai.backend.manager.cli.seed import cli
from ai.backend.manager.errors.seed import InvalidSeedDocument
from ai.backend.manager.seed.app_config_allow_list.seed import AppConfigAllowListSeed
from ai.backend.manager.seed.factory import create_seed_kind_registry
from ai.backend.manager.seed.runner import SeedPlanner


def _write(path: Path, *items: dict[str, Any]) -> Path:
    path.write_text(
        yaml.safe_dump({"kind": "app_config_allow_list", "version": 1, "items": list(items)})
    )
    return path


class TestAppConfigAllowListSeed:
    def test_the_key_is_the_config_name_and_scope_type(self) -> None:
        seed = AppConfigAllowListSeed.model_validate({
            "config_name": "webui",
            "scope_type": "domain",
        })
        assert seed.key() == "webui:domain"

    def test_the_rank_is_optional(self) -> None:
        seed = AppConfigAllowListSeed.model_validate({"config_name": "webui", "scope_type": "user"})
        assert seed.rank is None

    @pytest.mark.parametrize(
        "item",
        [
            {"scope_type": "public"},
            {"config_name": "webui"},
            {"config_name": "", "scope_type": "public"},
            {"config_name": "x" * 129, "scope_type": "public"},
            {"config_name": "webui", "scope_type": "project"},
            {"config_name": "webui", "scope_type": "public", "rank": 2**31},
            {"config_name": "webui", "scope_type": "public", "rank": -(2**31) - 1},
            {"config_name": "webui", "scope_type": "public", "id": "0198a5a0-0000-7000-8000-0"},
        ],
        ids=[
            "missing-name",
            "missing-scope-type",
            "empty-name",
            "too-long-name",
            "unknown-scope-type",
            "rank-too-large",
            "rank-too-small",
            "unknown-field",
        ],
    )
    def test_an_invalid_item_is_refused(self, item: dict[str, Any]) -> None:
        with pytest.raises(InvalidSeedDocument):
            AppConfigAllowListSeed.model_validate(item)


class TestAppConfigAllowListKind:
    def test_the_files_are_planned_whole(self, app_config_allow_list_seed_dir: Path) -> None:
        plan = SeedPlanner(create_seed_kind_registry()).plan([app_config_allow_list_seed_dir])
        assert plan.rejections == []
        assert [batch.kind.name for batch in plan.batches] == [
            "app_config_definition",
            "app_config_allow_list",
        ]
        assert [item.key() for item in plan.batches[1].items()] == [
            "webui:public",
            "webui:user",
            "session_launcher:domain",
        ]

    def test_an_entry_stated_in_two_files_skips_both(self, tmp_path: Path) -> None:
        first = _write(tmp_path / "first.yaml", {"config_name": "webui", "scope_type": "public"})
        second = _write(
            tmp_path / "second.yaml", {"config_name": "webui", "scope_type": "public", "rank": 1}
        )
        plan = SeedPlanner(create_seed_kind_registry()).plan([first, second])
        assert sorted(rejection.source for rejection in plan.rejections) == [
            str(first),
            str(second),
        ]
        assert plan.batches == []


class TestCheckCommand:
    def test_the_files_pass(self, app_config_allow_list_seed_dir: Path) -> None:
        result = CliRunner().invoke(cli, ["check", str(app_config_allow_list_seed_dir)])
        assert result.exit_code == 0, result.output
        assert "app_config_allow_list: 1 files, 3 items" in result.output

    def test_an_invalid_item_fails_the_command(self, tmp_path: Path) -> None:
        path = _write(tmp_path / "bad.yaml", {"config_name": "webui", "scope_type": "project"})
        result = CliRunner().invoke(cli, ["check", str(path)])
        assert result.exit_code != 0
