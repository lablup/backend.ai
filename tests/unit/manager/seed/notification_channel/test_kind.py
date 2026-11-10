"""The `notification_channel` kind reads one item per channel id, and `mgr seed check`
reports what it skips."""

from __future__ import annotations

from pathlib import Path
from typing import Any

import pytest
import yaml
from click.testing import CliRunner

from ai.backend.common.data.notification import WebhookSpec
from ai.backend.common.data.notification.types import EmailSpec
from ai.backend.manager.cli.seed import cli
from ai.backend.manager.errors.seed import InvalidSeedDocument
from ai.backend.manager.seed.factory import create_seed_kind_registry
from ai.backend.manager.seed.notification_channel.seed import NotificationChannelSeed
from ai.backend.manager.seed.runner import SeedPlanner

_ID = "0198a5a0-0000-7000-8000-00000000c101"
_CREATOR = "f38dea23-50fa-42a0-b5ae-338f5f4693f4"
_WEBHOOK: dict[str, Any] = {
    "id": _ID,
    "name": "ops-webhook",
    "channel_type": "webhook",
    "spec": {"url": "https://hooks.example.com/ops"},
    "created_by": _CREATOR,
}
_EMAIL_SPEC: dict[str, Any] = {
    "smtp": {"host": "smtp.example.com", "port": 587},
    "message": {"from_email": "noreply@example.com", "to_emails": ["ops@example.com"]},
}


def _write(path: Path, *items: dict[str, Any]) -> Path:
    path.write_text(
        yaml.safe_dump({"kind": "notification_channel", "version": 1, "items": list(items)})
    )
    return path


class TestNotificationChannelSeed:
    def test_the_key_is_the_id(self) -> None:
        seed = NotificationChannelSeed.model_validate(_WEBHOOK)
        assert seed.key() == _ID

    def test_a_webhook_spec_is_read_as_a_webhook(self) -> None:
        seed = NotificationChannelSeed.model_validate(_WEBHOOK)
        assert isinstance(seed.spec, WebhookSpec)
        assert seed.enabled is True

    def test_an_email_spec_is_read_as_an_email(self) -> None:
        seed = NotificationChannelSeed.model_validate(
            _WEBHOOK | {"channel_type": "email", "spec": _EMAIL_SPEC}
        )
        assert isinstance(seed.spec, EmailSpec)

    @pytest.mark.parametrize(
        "item",
        [
            {k: v for k, v in _WEBHOOK.items() if k != "id"},
            {k: v for k, v in _WEBHOOK.items() if k != "created_by"},
            _WEBHOOK | {"name": ""},
            _WEBHOOK | {"name": "x" * 257},
            _WEBHOOK | {"channel_type": "slack"},
            _WEBHOOK | {"channel_type": "email"},
            _WEBHOOK | {"spec": _EMAIL_SPEC},
            _WEBHOOK | {"owner": _CREATOR},
        ],
        ids=[
            "missing-id",
            "missing-created-by",
            "empty-name",
            "too-long-name",
            "unknown-channel-type",
            "webhook-spec-for-email",
            "email-spec-for-webhook",
            "unknown-field",
        ],
    )
    def test_an_invalid_item_is_refused(self, item: dict[str, Any]) -> None:
        with pytest.raises(InvalidSeedDocument):
            NotificationChannelSeed.model_validate(item)


class TestNotificationChannelKind:
    def test_the_files_are_planned_whole(self, notification_channel_seed_dir: Path) -> None:
        plan = SeedPlanner(create_seed_kind_registry()).plan([notification_channel_seed_dir])
        assert plan.rejections == []
        [batch] = plan.batches
        assert batch.kind.name == "notification_channel"
        assert [item.key() for item in batch.items()] == [
            "0198a5a0-0000-7000-8000-00000000c001",
            "0198a5a0-0000-7000-8000-00000000c002",
        ]

    def test_an_id_stated_in_two_files_skips_both(self, tmp_path: Path) -> None:
        first = _write(tmp_path / "first.yaml", _WEBHOOK)
        second = _write(tmp_path / "second.yaml", _WEBHOOK | {"name": "other"})
        plan = SeedPlanner(create_seed_kind_registry()).plan([first, second])
        assert sorted(rejection.source for rejection in plan.rejections) == [
            str(first),
            str(second),
        ]
        assert plan.batches == []


class TestCheckCommand:
    def test_the_files_pass(self, notification_channel_seed_dir: Path) -> None:
        result = CliRunner().invoke(cli, ["check", str(notification_channel_seed_dir)])
        assert result.exit_code == 0, result.output
        assert "notification_channel: 1 files, 2 items" in result.output

    def test_an_invalid_item_fails_the_command(self, tmp_path: Path) -> None:
        path = _write(tmp_path / "bad.yaml", _WEBHOOK | {"channel_type": "email"})
        result = CliRunner().invoke(cli, ["check", str(path)])
        assert result.exit_code != 0


class TestNotificationChannelSeedCheck:
    def test_an_item_keeping_the_rules_passes(self) -> None:
        assert NotificationChannelSeed.model_validate(_WEBHOOK).check() == []

    @pytest.mark.parametrize(
        "item",
        [
            {**_WEBHOOK, "name": "  "},
        ],
        ids=[
            "blank-name",
        ],
    )
    def test_an_item_breaking_a_rule_fails(self, item: dict[str, Any]) -> None:
        assert len(NotificationChannelSeed.model_validate(item).check()) == 1
