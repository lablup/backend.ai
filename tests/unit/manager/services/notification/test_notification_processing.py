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

from ai.backend.common.contexts.user import with_user
from ai.backend.common.data.entity.domain import DomainID
from ai.backend.common.data.entity.notification import (
    NOTIFICATION_CHANNEL_ENTITY_TYPE,
    NOTIFICATION_RULE_ENTITY_TYPE,
    NotificationChannelID,
    NotificationRuleID,
)
from ai.backend.common.data.notification import SessionStartedMessage
from ai.backend.common.data.notification.types import (
    NotificationChannelType,
    NotificationRuleType,
    WebhookSpec,
)
from ai.backend.common.data.user.types import UserData, UserRole
from ai.backend.manager.actions.registry import GroupMeta
from ai.backend.manager.data.notification import (
    NotificationChannelData,
    NotificationRuleData,
)
from ai.backend.manager.data.notification.types import MatchingNotificationRuleData
from ai.backend.manager.notification.notification_center import NotificationCenter
from ai.backend.manager.notification.types import SendResult
from ai.backend.manager.repositories.notification.repository import NotificationRepository
from ai.backend.manager.services.notification.actions import (
    ProcessNotificationAction,
    ProcessNotificationActionResult,
)
from ai.backend.manager.services.notification.processors import NotificationProcessors
from ai.backend.manager.services.notification.service import NotificationService
from ai.backend.testutils.processors import ops_processor_group


@pytest.fixture()
async def notification_center() -> AsyncGenerator[NotificationCenter, None]:
    nc = NotificationCenter()
    yield nc
    await nc.close()


@pytest.fixture()
def mock_repository() -> MagicMock:
    return MagicMock(spec=NotificationRepository)


@pytest.fixture()
def superadmin() -> UserData:
    """Dispatch runs behind the global processor's SUPERADMIN gate, so give it a caller."""
    return UserData(
        user_id=uuid.uuid4(),
        is_authorized=True,
        is_admin=True,
        is_superadmin=True,
        role=UserRole.SUPERADMIN,
        domain_name="default",
        domain_id=DomainID(uuid.uuid4()),
    )


@pytest.fixture()
def notification_processors(
    mock_repository: MagicMock,
    notification_center: NotificationCenter,
) -> NotificationProcessors:
    service = NotificationService(mock_repository, notification_center)
    # Only the dispatch path is exercised here; the ops-wired CRUD processors are
    # built but never reached, so the groups may sit on a stand-in engine.
    engine = MagicMock()
    return NotificationProcessors(
        channel_group=ops_processor_group(engine, GroupMeta(NOTIFICATION_CHANNEL_ENTITY_TYPE)),
        rule_group=ops_processor_group(engine, GroupMeta(NOTIFICATION_RULE_ENTITY_TYPE)),
        service=service,
    )


@pytest.fixture()
def sample_channel_data() -> NotificationChannelData:
    now = datetime.now(tz=UTC)
    return NotificationChannelData(
        id=NotificationChannelID(uuid.uuid4()),
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
        id=NotificationRuleID(uuid.uuid4()),
        name="fixture-notification-rule",
        description="Fixture rule for unit tests",
        rule_type=NotificationRuleType.SESSION_STARTED,
        channel_id=sample_channel_data.id,
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
        superadmin: UserData,
        notification_center: NotificationCenter,
        mock_repository: MagicMock,
        sample_rule_data: NotificationRuleData,
        sample_channel_data: NotificationChannelData,
    ) -> None:
        """A matching rule is found and the channel is called exactly once."""
        send_result = SendResult(message="Notification delivered")
        mock_repository.get_matching_rules = AsyncMock(
            return_value=[
                MatchingNotificationRuleData(rule=sample_rule_data, channel=sample_channel_data)
            ]
        )

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
            with with_user(superadmin):
                result = await notification_processors.process_notification.run(action)

        assert isinstance(result, ProcessNotificationActionResult)
        assert result.rules_matched >= 1
        assert len(result.successes) >= 1
        assert result.errors == []

    async def test_partial_channel_failure_tolerance(
        self,
        notification_processors: NotificationProcessors,
        superadmin: UserData,
        notification_center: NotificationCenter,
        mock_repository: MagicMock,
        sample_channel_data: NotificationChannelData,
    ) -> None:
        """When one channel send fails, other channels still receive the notification."""
        now = datetime.now(tz=UTC)
        channel2_data = NotificationChannelData(
            id=NotificationChannelID(uuid.uuid4()),
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
            id=NotificationRuleID(uuid.uuid4()),
            name="partial-fail-rule-1",
            description=None,
            rule_type=NotificationRuleType.SESSION_STARTED,
            channel_id=sample_channel_data.id,
            message_template="Rule 1: {{ session_name }}",
            enabled=True,
            created_by=uuid.uuid4(),
            created_at=now,
            updated_at=now,
        )
        rule2_data = NotificationRuleData(
            id=NotificationRuleID(uuid.uuid4()),
            name="partial-fail-rule-2",
            description=None,
            rule_type=NotificationRuleType.SESSION_STARTED,
            channel_id=channel2_data.id,
            message_template="Rule 2: {{ session_name }}",
            enabled=True,
            created_by=uuid.uuid4(),
            created_at=now,
            updated_at=now,
        )
        mock_repository.get_matching_rules = AsyncMock(
            return_value=[
                MatchingNotificationRuleData(rule=rule1_data, channel=sample_channel_data),
                MatchingNotificationRuleData(rule=rule2_data, channel=sample_channel_data),
            ]
        )

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
            with with_user(superadmin):
                result = await notification_processors.process_notification.run(action)

        assert isinstance(result, ProcessNotificationActionResult)
        assert result.rules_matched >= 2
        assert len(result.successes) >= 1
        assert len(result.errors) >= 1
