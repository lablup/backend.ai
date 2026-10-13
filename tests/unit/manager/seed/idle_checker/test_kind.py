"""The `idle_checker` kind reads one item per checker id, and `mgr seed check` reports
what it skips."""

from __future__ import annotations

from pathlib import Path
from typing import Any

import pytest
import yaml
from click.testing import CliRunner

from ai.backend.manager.cli.seed import cli
from ai.backend.manager.errors.seed import InvalidSeedDocument
from ai.backend.manager.seed.factory import create_seed_kind_registry
from ai.backend.manager.seed.idle_checker.seed import IdleCheckerSeed
from ai.backend.manager.seed.runner import SeedPlanner

_ID = "0198a5a0-0000-7000-8000-00000000f001"
_ITEM: dict[str, Any] = {
    "id": _ID,
    "name": "session-lifetime",
    "target_session_types": ["interactive"],
    "spec": {"type": "session_lifetime", "session_lifetime": {"max_lifetime_seconds": 60}},
}


def _write(path: Path, *items: dict[str, Any]) -> Path:
    path.write_text(yaml.safe_dump({"kind": "idle_checker", "version": 1, "items": list(items)}))
    return path


class TestIdleCheckerSeed:
    def test_the_key_is_the_id(self) -> None:
        seed = IdleCheckerSeed.model_validate(_ITEM)
        assert seed.key() == _ID

    def test_the_grace_period_defaults_to_zero(self) -> None:
        seed = IdleCheckerSeed.model_validate(_ITEM)
        assert seed.initial_grace_period_seconds == 0
        assert seed.description is None

    @pytest.mark.parametrize(
        "change",
        [
            {"id": None},
            {"name": ""},
            {"name": "x" * 129},
            {"target_session_types": []},
            {"target_session_types": ["unknown"]},
            {"initial_grace_period_seconds": -1},
            {"spec": {"type": "session_lifetime"}},
            {"spec": {"type": "network_timeout", "session_lifetime": {"max_lifetime_seconds": 60}}},
            {"checker_type": "session_lifetime"},
        ],
        ids=[
            "missing-id",
            "empty-name",
            "too-long-name",
            "no-session-type",
            "unknown-session-type",
            "negative-grace-period",
            "spec-without-config",
            "spec-of-another-type",
            "unknown-field",
        ],
    )
    def test_an_invalid_item_is_refused(self, change: dict[str, Any]) -> None:
        item = {key: value for key, value in (_ITEM | change).items() if value is not None}
        with pytest.raises(InvalidSeedDocument):
            IdleCheckerSeed.model_validate(item)


class TestIdleCheckerKind:
    def test_the_files_are_planned_whole(
        self, idle_checker_seed_dir: Path, idle_checker_ids: list[str]
    ) -> None:
        plan = SeedPlanner(create_seed_kind_registry()).plan([idle_checker_seed_dir])
        assert plan.rejections == []
        [batch] = plan.batches
        assert batch.kind.name == "idle_checker"
        assert [item.key() for item in batch.items()] == idle_checker_ids

    def test_an_id_stated_in_two_files_skips_both(self, tmp_path: Path) -> None:
        first = _write(tmp_path / "first.yaml", _ITEM)
        second = _write(tmp_path / "second.yaml", _ITEM | {"name": "other"})
        plan = SeedPlanner(create_seed_kind_registry()).plan([first, second])
        assert sorted(rejection.source for rejection in plan.rejections) == [
            str(first),
            str(second),
        ]
        assert plan.batches == []


class TestCheckCommand:
    def test_the_files_pass(self, idle_checker_seed_dir: Path) -> None:
        result = CliRunner().invoke(cli, ["check", str(idle_checker_seed_dir)])
        assert result.exit_code == 0, result.output
        assert "idle_checker: 1 files, 2 items" in result.output

    def test_an_invalid_item_fails_the_command(self, tmp_path: Path) -> None:
        path = _write(tmp_path / "bad.yaml", _ITEM | {"initial_grace_period_seconds": -1})
        result = CliRunner().invoke(cli, ["check", str(path)])
        assert result.exit_code != 0
