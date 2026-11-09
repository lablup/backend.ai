"""The `login_client_type` kind reads one item per id, and `mgr seed check` reports what it
skips."""

from __future__ import annotations

from pathlib import Path
from typing import Any

import pytest
import yaml
from click.testing import CliRunner

from ai.backend.manager.cli.seed import cli
from ai.backend.manager.errors.seed import InvalidSeedDocument
from ai.backend.manager.seed.factory import create_seed_kind_registry
from ai.backend.manager.seed.login_client_type.seed import LoginClientTypeSeed
from ai.backend.manager.seed.runner import SeedPlanner

_ID = "0198a5a0-0000-7000-8000-00000000c001"


def _write(path: Path, *items: dict[str, Any]) -> Path:
    path.write_text(
        yaml.safe_dump({"kind": "login_client_type", "version": 1, "items": list(items)})
    )
    return path


class TestLoginClientTypeSeed:
    def test_the_key_is_the_id(self) -> None:
        seed = LoginClientTypeSeed.model_validate({"id": _ID, "name": "webui"})
        assert seed.key() == _ID

    def test_the_description_defaults_to_none(self) -> None:
        seed = LoginClientTypeSeed.model_validate({"id": _ID, "name": "webui"})
        assert seed.description is None

    @pytest.mark.parametrize(
        "item",
        [
            {"name": "webui"},
            {"id": "not-a-uuid", "name": "webui"},
            {"id": _ID},
            {"id": _ID, "name": ""},
            {"id": _ID, "name": "x" * 65},
            {"id": _ID, "name": "webui", "extra": 1},
        ],
        ids=["missing-id", "invalid-id", "missing-name", "empty-name", "too-long", "unknown-field"],
    )
    def test_an_invalid_item_is_refused(self, item: dict[str, Any]) -> None:
        with pytest.raises(InvalidSeedDocument):
            LoginClientTypeSeed.model_validate(item)


class TestLoginClientTypeKind:
    def test_the_files_are_planned_whole(self, login_client_type_seed_dir: Path) -> None:
        plan = SeedPlanner(create_seed_kind_registry()).plan([login_client_type_seed_dir])
        assert plan.rejections == []
        [batch] = plan.batches
        assert batch.kind.name == "login_client_type"
        assert [item.key() for item in batch.items()] == [
            "0198a5a0-0000-7000-8000-00000000c001",
            "0198a5a0-0000-7000-8000-00000000c002",
        ]

    def test_an_id_stated_in_two_files_skips_both(self, tmp_path: Path) -> None:
        first = _write(tmp_path / "first.yaml", {"id": _ID, "name": "webui"})
        second = _write(tmp_path / "second.yaml", {"id": _ID, "name": "cli"})
        plan = SeedPlanner(create_seed_kind_registry()).plan([first, second])
        assert sorted(rejection.source for rejection in plan.rejections) == [
            str(first),
            str(second),
        ]
        assert plan.batches == []


class TestCheckCommand:
    def test_the_files_pass(self, login_client_type_seed_dir: Path) -> None:
        result = CliRunner().invoke(cli, ["check", str(login_client_type_seed_dir)])
        assert result.exit_code == 0, result.output
        assert "login_client_type: 1 files, 2 items" in result.output

    def test_an_invalid_item_fails_the_command(self, tmp_path: Path) -> None:
        path = _write(tmp_path / "bad.yaml", {"id": _ID, "name": ""})
        result = CliRunner().invoke(cli, ["check", str(path)])
        assert result.exit_code != 0
