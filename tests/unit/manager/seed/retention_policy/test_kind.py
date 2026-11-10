"""The `retention_policy` kind reads one item per policy id, and `mgr seed check` reports
what it skips."""

from __future__ import annotations

from datetime import timedelta
from pathlib import Path
from typing import Any

import pytest
import yaml
from click.testing import CliRunner

from ai.backend.common.data.retention.types import RetentionCategory
from ai.backend.manager.cli.seed import cli
from ai.backend.manager.errors.seed import InvalidSeedDocument
from ai.backend.manager.seed.factory import create_seed_kind_registry
from ai.backend.manager.seed.retention_policy.seed import RetentionPolicySeed
from ai.backend.manager.seed.runner import SeedPlanner

_LOGS: dict[str, Any] = {
    "id": "0198a5a0-0000-7000-8000-00000000d001",
    "category": "logs",
    "retention_period_days": 365,
    "enabled": False,
}


def _write(path: Path, *items: dict[str, Any]) -> Path:
    path.write_text(
        yaml.safe_dump({"kind": "retention_policy", "version": 1, "items": list(items)})
    )
    return path


class TestRetentionPolicySeed:
    def test_the_key_is_the_id(self) -> None:
        seed = RetentionPolicySeed.model_validate(_LOGS)
        assert seed.key() == _LOGS["id"]

    def test_the_period_is_written_in_days(self) -> None:
        upserter = RetentionPolicySeed.model_validate(_LOGS).write().upserter
        assert upserter.build_insert_values() == {
            "id": RetentionPolicySeed.model_validate(_LOGS).id,
            "category": RetentionCategory.LOGS,
            "retention_period": timedelta(days=365),
            "enabled": False,
        }

    @pytest.mark.parametrize(
        "item",
        [
            {key: value for key, value in _LOGS.items() if key != "id"},
            _LOGS | {"id": "not-a-uuid"},
            _LOGS | {"category": "unknown"},
            _LOGS | {"retention_period_days": 0},
            _LOGS | {"retention_period_days": -1},
            _LOGS | {"retention_period_days": timedelta.max.days + 1},
            _LOGS | {"last_swept_at": "2026-01-01T00:00:00Z"},
        ],
        ids=[
            "missing-id",
            "bad-id",
            "unknown-category",
            "zero-days",
            "negative-days",
            "over-timedelta",
            "unknown",
        ],
    )
    def test_an_invalid_item_is_refused(self, item: dict[str, Any]) -> None:
        with pytest.raises(InvalidSeedDocument):
            RetentionPolicySeed.model_validate(item)


class TestRetentionPolicyKind:
    def test_the_files_are_planned_whole(self, retention_policy_seed_dir: Path) -> None:
        plan = SeedPlanner(create_seed_kind_registry()).plan([retention_policy_seed_dir])
        assert plan.rejections == []
        [batch] = plan.batches
        assert batch.kind.name == "retention_policy"
        assert [item.key() for item in batch.items()] == [
            "0198a5a0-0000-7000-8000-00000000d001",
            "0198a5a0-0000-7000-8000-00000000d002",
        ]

    def test_an_id_stated_in_two_files_skips_both(self, tmp_path: Path) -> None:
        first = _write(tmp_path / "first.yaml", _LOGS)
        second = _write(tmp_path / "second.yaml", _LOGS)
        plan = SeedPlanner(create_seed_kind_registry()).plan([first, second])
        assert sorted(rejection.source for rejection in plan.rejections) == [
            str(first),
            str(second),
        ]
        assert plan.batches == []


class TestCheckCommand:
    def test_the_files_pass(self, retention_policy_seed_dir: Path) -> None:
        result = CliRunner().invoke(cli, ["check", str(retention_policy_seed_dir)])
        assert result.exit_code == 0, result.output
        assert "retention_policy: 1 files, 2 items" in result.output

    def test_an_invalid_item_fails_the_command(self, tmp_path: Path) -> None:
        path = _write(tmp_path / "bad.yaml", _LOGS | {"retention_period_days": 0})
        result = CliRunner().invoke(cli, ["check", str(path)])
        assert result.exit_code != 0
