"""The `notification_rule` kind reads one item per rule id, and `mgr seed check` reports
what it skips."""

from __future__ import annotations

from pathlib import Path
from typing import Any

import pytest
import yaml
from click.testing import CliRunner

from ai.backend.common.data.notification import NotificationRuleType
from ai.backend.manager.cli.seed import cli
from ai.backend.manager.errors.seed import InvalidSeedDocument
from ai.backend.manager.seed.factory import create_seed_kind_registry
from ai.backend.manager.seed.notification_rule.seed import NotificationRuleSeed
from ai.backend.manager.seed.runner import SeedPlanner

_ID = "0198a5a0-0000-7000-8000-00000000d101"
_CREATOR = "f38dea23-50fa-42a0-b5ae-338f5f4693f4"
_RULE: dict[str, Any] = {
    "id": _ID,
    "name": "session-started",
    "rule_type": "session.started",
    "channel_id": "0198a5a0-0000-7000-8000-00000000c101",
    "message_template": "Session {{ session_id }} started",
    "created_by": _CREATOR,
}


def _write(path: Path, *items: dict[str, Any]) -> Path:
    path.write_text(
        yaml.safe_dump({"kind": "notification_rule", "version": 1, "items": list(items)})
    )
    return path


class TestNotificationRuleSeed:
    def test_the_key_is_the_id(self) -> None:
        seed = NotificationRuleSeed.model_validate(_RULE)
        assert seed.key() == _ID

    def test_the_rule_type_is_read_and_the_rule_is_enabled(self) -> None:
        seed = NotificationRuleSeed.model_validate(_RULE)
        assert seed.rule_type == NotificationRuleType.SESSION_STARTED
        assert seed.enabled is True

    @pytest.mark.parametrize(
        "item",
        [
            {k: v for k, v in _RULE.items() if k != "id"},
            {k: v for k, v in _RULE.items() if k != "channel_id"},
            {k: v for k, v in _RULE.items() if k != "message_template"},
            {k: v for k, v in _RULE.items() if k != "created_by"},
            _RULE | {"name": ""},
            _RULE | {"name": "x" * 257},
            _RULE | {"message_template": "x" * 65537},
            _RULE | {"rule_type": "session.paused"},
            _RULE | {"owner": _CREATOR},
        ],
        ids=[
            "missing-id",
            "missing-channel-id",
            "missing-message-template",
            "missing-created-by",
            "empty-name",
            "too-long-name",
            "too-long-message-template",
            "unknown-rule-type",
            "unknown-field",
        ],
    )
    def test_an_invalid_item_is_refused(self, item: dict[str, Any]) -> None:
        with pytest.raises(InvalidSeedDocument):
            NotificationRuleSeed.model_validate(item)


class TestNotificationRuleKind:
    def test_the_files_are_planned_whole(self, notification_rule_seed_dir: Path) -> None:
        plan = SeedPlanner(create_seed_kind_registry()).plan([notification_rule_seed_dir])
        assert plan.rejections == []
        [batch] = plan.batches
        assert batch.kind.name == "notification_rule"
        assert [item.key() for item in batch.items()] == [
            "0198a5a0-0000-7000-8000-00000000d001",
            "0198a5a0-0000-7000-8000-00000000d002",
        ]

    def test_an_id_stated_in_two_files_skips_both(self, tmp_path: Path) -> None:
        first = _write(tmp_path / "first.yaml", _RULE)
        second = _write(tmp_path / "second.yaml", _RULE | {"name": "other"})
        plan = SeedPlanner(create_seed_kind_registry()).plan([first, second])
        assert sorted(rejection.source for rejection in plan.rejections) == [
            str(first),
            str(second),
        ]
        assert plan.batches == []


class TestCheckCommand:
    def test_the_files_pass(self, notification_rule_seed_dir: Path) -> None:
        result = CliRunner().invoke(cli, ["check", str(notification_rule_seed_dir)])
        assert result.exit_code == 0, result.output
        assert "notification_rule: 1 files, 2 items" in result.output

    def test_an_invalid_item_fails_the_command(self, tmp_path: Path) -> None:
        path = _write(tmp_path / "bad.yaml", _RULE | {"rule_type": "session.paused"})
        result = CliRunner().invoke(cli, ["check", str(path)])
        assert result.exit_code != 0
