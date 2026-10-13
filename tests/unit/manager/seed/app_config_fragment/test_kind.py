"""The `app_config_fragment` kind reads one item per config name and scope, and
`mgr seed check` reports what it skips."""

from __future__ import annotations

from pathlib import Path
from typing import Any

import pytest
import yaml
from click.testing import CliRunner

from ai.backend.manager.cli.seed import cli
from ai.backend.manager.errors.seed import InvalidSeedDocument
from ai.backend.manager.seed.app_config_fragment.seed import AppConfigFragmentSeed
from ai.backend.manager.seed.factory import create_seed_kind_registry
from ai.backend.manager.seed.runner import SeedPlanner

_DOMAIN_ID = "0198a5a0-0000-7000-8000-00000000d001"


def _write(path: Path, *items: dict[str, Any]) -> Path:
    path.write_text(
        yaml.safe_dump({"kind": "app_config_fragment", "version": 1, "items": list(items)})
    )
    return path


class TestAppConfigFragmentSeed:
    def test_a_public_key_is_the_config_name_and_scope_type(self) -> None:
        seed = AppConfigFragmentSeed.model_validate({
            "config_name": "webui",
            "scope_type": "public",
            "config": {},
        })
        assert seed.key() == "webui:public"

    def test_a_scoped_key_adds_the_scope_id(self) -> None:
        seed = AppConfigFragmentSeed.model_validate({
            "config_name": "webui",
            "scope_type": "domain",
            "scope_id": _DOMAIN_ID,
            "config": {},
        })
        assert seed.key() == f"webui:domain:{_DOMAIN_ID}"

    @pytest.mark.parametrize(
        "item",
        [
            {"scope_type": "public", "config": {}},
            {"config_name": "webui", "config": {}},
            {"config_name": "webui", "scope_type": "public"},
            {"config_name": "", "scope_type": "public", "config": {}},
            {"config_name": "x" * 129, "scope_type": "public", "config": {}},
            {"config_name": "webui", "scope_type": "project", "config": {}},
            {"config_name": "webui", "scope_type": "public", "scope_id": _DOMAIN_ID, "config": {}},
            {"config_name": "webui", "scope_type": "domain", "config": {}},
            {"config_name": "webui", "scope_type": "user", "config": {}},
            {"config_name": "webui", "scope_type": "domain", "scope_id": "x", "config": {}},
            {"config_name": "webui", "scope_type": "public", "config": []},
            {"config_name": "webui", "scope_type": "public", "config": {}, "rank": 1},
        ],
        ids=[
            "missing-name",
            "missing-scope-type",
            "missing-config",
            "empty-name",
            "too-long-name",
            "unknown-scope-type",
            "public-with-scope-id",
            "domain-without-scope-id",
            "user-without-scope-id",
            "malformed-scope-id",
            "config-not-a-mapping",
            "unknown-field",
        ],
    )
    def test_an_invalid_item_is_refused(self, item: dict[str, Any]) -> None:
        with pytest.raises(InvalidSeedDocument):
            AppConfigFragmentSeed.model_validate(item)


class TestAppConfigFragmentKind:
    def test_the_files_are_planned_whole(self, app_config_fragment_seed_dir: Path) -> None:
        plan = SeedPlanner(create_seed_kind_registry()).plan([app_config_fragment_seed_dir])
        assert plan.rejections == []
        assert [batch.kind.name for batch in plan.batches] == [
            "app_config_definition",
            "app_config_allow_list",
            "domain",
            "app_config_fragment",
        ]
        assert [item.key() for item in plan.batches[3].items()] == [
            "webui:public",
            f"session_launcher:domain:{_DOMAIN_ID}",
        ]

    def test_a_fragment_stated_in_two_files_skips_both(self, tmp_path: Path) -> None:
        item = {"config_name": "webui", "scope_type": "public", "config": {}}
        first = _write(tmp_path / "first.yaml", item)
        second = _write(tmp_path / "second.yaml", item | {"config": {"theme": "dark"}})
        plan = SeedPlanner(create_seed_kind_registry()).plan([first, second])
        assert sorted(rejection.source for rejection in plan.rejections) == [
            str(first),
            str(second),
        ]
        assert plan.batches == []


class TestCheckCommand:
    def test_the_files_pass(self, app_config_fragment_seed_dir: Path) -> None:
        result = CliRunner().invoke(cli, ["check", str(app_config_fragment_seed_dir)])
        assert result.exit_code == 0, result.output
        assert "app_config_fragment: 1 files, 2 items" in result.output

    def test_an_invalid_item_fails_the_command(self, tmp_path: Path) -> None:
        path = _write(
            tmp_path / "bad.yaml", {"config_name": "webui", "scope_type": "domain", "config": {}}
        )
        result = CliRunner().invoke(cli, ["check", str(path)])
        assert result.exit_code != 0
