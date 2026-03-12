"""
Unit tests for NotificationProcessors.process_notification.

Tests the processing pipeline with a mocked repository — no real DB or HTTP server.
The component equivalents (TestChannelCreate, TestRuleCreate, etc.) live in
tests/component/notification/test_notification.py and exercise the HTTP API layer.
"""

from __future__ import annotations

import uuid
from collections.abc import AsyncGenerator
from datetime import UTC, datetime
from unittest.mock import AsyncMock, MagicMock, patch

import pytest

from ai.backend.common.data.notification import SessionStartedMessage
from ai.backend.common.data.notification.types import (
    NotificationChannelType,
    NotificationRuleType,
    WebhookSpec,
)
from ai.backend.manager.actions.validators import ActionValidators
from ai.backend.manager.data.notification import (
    NotificationChannelData,
    NotificationRuleData,
)
from ai.backend.manager.notification.notification_center import NotificationCenter
from ai.backend.manager.notification.types import SendResult
from ai.backend.manager.repositories.notification.repository import NotificationRepository
from ai.backend.manager.services.notification.actions import (
    ProcessNotificationAction,
    ProcessNotificationActionResult,
)
from ai.backend.manager.services.notification.processors import NotificationProcessors
from ai.backend.manager.services.notification.service import NotificationService


@pytest.fixture()
async def notification_center() -> AsyncGenerator[NotificationCenter, None]:
    nc = NotificationCenter()
    yield nc
    await nc.close()


@pytest.fixture()
def mock_repository() -> MagicMock:
    return MagicMock(spec=NotificationRepository)


@pytest.fixture()
def notification_processors(
    mock_repository: MagicMock,
    notification_center: NotificationCenter,
) -> NotificationProcessors:
    service = NotificationService(mock_repository, notification_center)
    return NotificationProcessors(
        service=service, action_monitors=[], validators=MagicMock(spec=ActionValidators)
    )


@pytest.fixture()
def sample_channel_data() -> NotificationChannelData:
    now = datetime.now(tz=UTC)
    return NotificationChannelData(
        id=uuid.uuid4(),
        name="test-webhook",
        description="Test webhook channel",
        channel_type=NotificationChannelType.WEBHOOK,
        spec=WebhookSpec(url="https://example.com/webhook"),
        enabled=True,
        created_by=uuid.uuid4(),
        created_at=now,
        updated_at=now,
    )


@pytest.fixture()
def sample_rule_data(sample_channel_data: NotificationChannelData) -> NotificationRuleData:
    now = datetime.now(tz=UTC)
    return NotificationRuleData(
        id=uuid.uuid4(),
        name="fixture-notification-rule",
        description="Fixture rule for unit tests",
        rule_type=NotificationRuleType.SESSION_STARTED,
        channel=sample_channel_data,
        message_template="Session {{ session_name }} started ({{ session_type }})",
        enabled=True,
        created_by=uuid.uuid4(),
        created_at=now,
        updated_at=now,
    )


class TestNotificationProcessing:
    async def test_event_triggers_matching_rule(
        self,
        notification_processors: NotificationProcessors,
        notification_center: NotificationCenter,
        mock_repository: MagicMock,
        sample_rule_data: NotificationRuleData,
    ) -> None:
        """A matching rule is found and the channel is called exactly once."""
        send_result = SendResult(message="Notification delivered")
        mock_repository.get_matching_rules = AsyncMock(return_value=[sample_rule_data])

        with patch.object(
            notification_center,
            "process_rule",
            new=AsyncMock(return_value=send_result),
        ):
            action = ProcessNotificationAction(
                rule_type=NotificationRuleType.SESSION_STARTED,
                timestamp=datetime.now(UTC),
                notification_data=SessionStartedMessage(
                    session_id=str(uuid.uuid4()),
                    session_name="test-session",
                    session_type="interactive",
                    cluster_mode="single-node",
                    status="RUNNING",
                ),
            )
            result = await notification_processors.process_notification.wait_for_complete(action)

        assert isinstance(result, ProcessNotificationActionResult)
        assert result.rules_matched >= 1
        assert len(result.successes) >= 1
        assert result.errors == []

    async def test_partial_channel_failure_tolerance(
        self,
        notification_processors: NotificationProcessors,
        notification_center: NotificationCenter,
        mock_repository: MagicMock,
        sample_channel_data: NotificationChannelData,
    ) -> None:
        """When one channel send fails, other channels still receive the notification."""
        now = datetime.now(tz=UTC)
        channel2_data = NotificationChannelData(
            id=uuid.uuid4(),
            name="partial-failure-channel-2",
            description="Second channel for partial failure test",
            channel_type=NotificationChannelType.WEBHOOK,
            spec=WebhookSpec(url="https://example.com/webhook2"),
            enabled=True,
            created_by=uuid.uuid4(),
            created_at=now,
            updated_at=now,
        )
        rule1_data = NotificationRuleData(
            id=uuid.uuid4(),
            name="partial-fail-rule-1",
            description=None,
            rule_type=NotificationRuleType.SESSION_STARTED,
            channel=sample_channel_data,
            message_template="Rule 1: {{ session_name }}",
            enabled=True,
            created_by=uuid.uuid4(),
            created_at=now,
            updated_at=now,
        )
        rule2_data = NotificationRuleData(
            id=uuid.uuid4(),
            name="partial-fail-rule-2",
            description=None,
            rule_type=NotificationRuleType.SESSION_STARTED,
            channel=channel2_data,
            message_template="Rule 2: {{ session_name }}",
            enabled=True,
            created_by=uuid.uuid4(),
            created_at=now,
            updated_at=now,
        )
        mock_repository.get_matching_rules = AsyncMock(return_value=[rule1_data, rule2_data])

        call_count = 0
        send_result = SendResult(message="ok")

        async def _mock_process_rule(*_args: object, **_kwargs: object) -> SendResult:
            nonlocal call_count
            call_count += 1
            if call_count == 1:
                return send_result
            raise RuntimeError("Simulated channel failure")

        with patch.object(
            notification_center,
            "process_rule",
            new=AsyncMock(side_effect=_mock_process_rule),
        ):
            action = ProcessNotificationAction(
                rule_type=NotificationRuleType.SESSION_STARTED,
                timestamp=datetime.now(UTC),
                notification_data=SessionStartedMessage(
                    session_id=str(uuid.uuid4()),
                    session_name="partial-session",
                    session_type="batch",
                    cluster_mode="single-node",
                    status="RUNNING",
                ),
            )
            result = await notification_processors.process_notification.wait_for_complete(action)

        assert isinstance(result, ProcessNotificationActionResult)
        assert result.rules_matched >= 2
        assert len(result.successes) >= 1
        assert len(result.errors) >= 1
