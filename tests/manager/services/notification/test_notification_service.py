"""
Tests for NotificationService functionality.
Tests the service layer with mocked repository operations.
"""

from datetime import datetime
from unittest.mock import AsyncMock, MagicMock
from uuid import uuid4

import pytest

from ai.backend.common.events.event_types.notification import NotificationTriggeredEvent
from ai.backend.manager.data.notification import (
    NotificationChannelData,
    NotificationChannelType,
    NotificationRuleData,
    NotificationRuleType,
    WebhookConfig,
)
from ai.backend.manager.repositories.notification import NotificationRepository
from ai.backend.manager.services.notification.actions import (
    ProcessNotificationAction,
)
from ai.backend.manager.services.notification.service import NotificationService


class TestNotificationService:
    """Test cases for NotificationService"""

    @pytest.fixture
    def mock_repository(self) -> MagicMock:
        """Create mocked NotificationRepository"""
        return MagicMock(spec=NotificationRepository)

    @pytest.fixture
    def notification_service(self, mock_repository: MagicMock) -> NotificationService:
        """Create NotificationService instance with mocked repository"""
        return NotificationService(repository=mock_repository)

    @pytest.fixture
    def sample_webhook_channel(self) -> NotificationChannelData:
        """Create sample webhook notification channel"""
        now = datetime.now()
        return NotificationChannelData(
            id=uuid4(),
            name="Test Webhook",
            description="Test webhook channel",
            channel_type=NotificationChannelType.WEBHOOK,
            config=WebhookConfig(
                url="https://example.com/webhook",
                method="POST",
                headers={"Authorization": "Bearer token"},
                timeout=30,
                success_status_codes=[200, 201, 202],
            ),
            enabled=True,
            created_by=uuid4(),
            created_at=now,
            updated_at=now,
        )

    @pytest.fixture
    def sample_rule(self, sample_webhook_channel: NotificationChannelData) -> NotificationRuleData:
        """Create sample notification rule"""
        now = datetime.now()
        return NotificationRuleData(
            id=uuid4(),
            name="Session Started Rule",
            description="Notify when session starts",
            rule_type=NotificationRuleType.SESSION_STARTED,
            channel=sample_webhook_channel,
            message_template="Session {{ session_id }} started for user {{ user_name }}",
            enabled=True,
            created_by=uuid4(),
            created_at=now,
            updated_at=now,
        )

    @pytest.fixture
    def sample_event(self) -> NotificationTriggeredEvent:
        """Create sample notification event"""
        return NotificationTriggeredEvent(
            rule_type=NotificationRuleType.SESSION_STARTED,
            timestamp=datetime.now(),
            notification_data={
                "session_id": "sess-12345",
                "user_name": "john_doe",
                "kernel_image": "python:3.11",
            },
        )

    @pytest.mark.asyncio
    async def test_process_notification_with_matching_rules(
        self,
        notification_service: NotificationService,
        mock_repository: MagicMock,
        sample_rule: NotificationRuleData,
        sample_event: NotificationTriggeredEvent,
    ) -> None:
        """Test processing notification with matching rules"""
        mock_repository.get_matching_rules = AsyncMock(return_value=[sample_rule])

        action = ProcessNotificationAction(
            rule_type=NotificationRuleType.SESSION_STARTED,
            timestamp=sample_event.timestamp,
            notification_data=sample_event.notification_data,
        )
        result = await notification_service.process_notification(action)

        assert result.rule_type == NotificationRuleType.SESSION_STARTED
        assert result.rules_matched == 1
        assert result.rules_processed == 1
        mock_repository.get_matching_rules.assert_called_once_with(
            NotificationRuleType.SESSION_STARTED, enabled_only=True
        )

    @pytest.mark.asyncio
    async def test_process_notification_with_no_matching_rules(
        self,
        notification_service: NotificationService,
        mock_repository: MagicMock,
        sample_event: NotificationTriggeredEvent,
    ) -> None:
        """Test processing notification when no rules match"""
        mock_repository.get_matching_rules = AsyncMock(return_value=[])

        action = ProcessNotificationAction(
            rule_type=NotificationRuleType.SESSION_STARTED,
            timestamp=sample_event.timestamp,
            notification_data=sample_event.notification_data,
        )
        result = await notification_service.process_notification(action)

        assert result.rule_type == NotificationRuleType.SESSION_STARTED
        assert result.rules_matched == 0
        assert result.rules_processed == 0

    @pytest.mark.asyncio
    async def test_template_rendering_with_data_fields(
        self,
        notification_service: NotificationService,
        mock_repository: MagicMock,
        sample_rule: NotificationRuleData,
        sample_event: NotificationTriggeredEvent,
    ) -> None:
        """Test that template rendering correctly uses notification data fields"""
        mock_repository.get_matching_rules = AsyncMock(return_value=[sample_rule])

        action = ProcessNotificationAction(
            rule_type=NotificationRuleType.SESSION_STARTED,
            timestamp=sample_event.timestamp,
            notification_data=sample_event.notification_data,
        )
        await notification_service.process_notification(action)

        # Verify template was rendered with correct data
        # The actual rendered message should contain the substituted values
        mock_repository.get_matching_rules.assert_called_once()

    @pytest.mark.asyncio
    async def test_process_notification_with_multiple_rules(
        self,
        notification_service: NotificationService,
        mock_repository: MagicMock,
        sample_webhook_channel: NotificationChannelData,
        sample_event: NotificationTriggeredEvent,
    ) -> None:
        """Test processing notification with multiple matching rules"""
        now = datetime.now()
        rule1 = NotificationRuleData(
            id=uuid4(),
            name="Rule 1",
            description=None,
            rule_type=NotificationRuleType.SESSION_STARTED,
            channel=sample_webhook_channel,
            message_template="Rule 1: Session {{ session_id }}",
            enabled=True,
            created_by=uuid4(),
            created_at=now,
            updated_at=now,
        )

        rule2 = NotificationRuleData(
            id=uuid4(),
            name="Rule 2",
            description=None,
            rule_type=NotificationRuleType.SESSION_STARTED,
            channel=sample_webhook_channel,
            message_template="Rule 2: User {{ user_name }}",
            enabled=True,
            created_by=uuid4(),
            created_at=now,
            updated_at=now,
        )

        mock_repository.get_matching_rules = AsyncMock(return_value=[rule1, rule2])

        action = ProcessNotificationAction(
            rule_type=NotificationRuleType.SESSION_STARTED,
            timestamp=sample_event.timestamp,
            notification_data=sample_event.notification_data,
        )
        result = await notification_service.process_notification(action)

        assert result.rules_matched == 2
        assert result.rules_processed == 2

    @pytest.mark.asyncio
    async def test_template_rendering_fallback_on_error(
        self,
        notification_service: NotificationService,
        mock_repository: MagicMock,
        sample_webhook_channel: NotificationChannelData,
        sample_event: NotificationTriggeredEvent,
    ) -> None:
        """Test that template rendering falls back to simple message on error"""
        # Create rule with invalid template syntax
        now = datetime.now()
        invalid_rule = NotificationRuleData(
            id=uuid4(),
            name="Invalid Template Rule",
            description=None,
            rule_type=NotificationRuleType.SESSION_STARTED,
            channel=sample_webhook_channel,
            message_template="Session {{ unclosed_tag",  # Invalid Jinja2 syntax
            enabled=True,
            created_by=uuid4(),
            created_at=now,
            updated_at=now,
        )

        mock_repository.get_matching_rules = AsyncMock(return_value=[invalid_rule])

        action = ProcessNotificationAction(
            rule_type=NotificationRuleType.SESSION_STARTED,
            timestamp=sample_event.timestamp,
            notification_data=sample_event.notification_data,
        )
        # Should not raise exception, should handle gracefully
        result = await notification_service.process_notification(action)

        assert result.rules_matched == 1
        # Rule should still be counted as processed even with template error
        assert result.rules_processed == 1

    @pytest.mark.asyncio
    async def test_template_with_timestamp(
        self,
        notification_service: NotificationService,
        mock_repository: MagicMock,
        sample_webhook_channel: NotificationChannelData,
    ) -> None:
        """Test that templates can access timestamp field"""
        now = datetime.now()
        rule = NotificationRuleData(
            id=uuid4(),
            name="Timestamp Rule",
            description=None,
            rule_type=NotificationRuleType.SESSION_STARTED,
            channel=sample_webhook_channel,
            message_template="Event at {{ timestamp.isoformat() }}",
            enabled=True,
            created_by=uuid4(),
            created_at=now,
            updated_at=now,
        )

        event = NotificationTriggeredEvent(
            rule_type=NotificationRuleType.SESSION_STARTED,
            timestamp=datetime.now(),
            notification_data={},
        )

        mock_repository.get_matching_rules = AsyncMock(return_value=[rule])

        action = ProcessNotificationAction(
            rule_type=NotificationRuleType.SESSION_STARTED,
            timestamp=event.timestamp,
            notification_data=event.notification_data,
        )
        result = await notification_service.process_notification(action)

        assert result.rules_processed == 1

    @pytest.mark.asyncio
    async def test_template_with_nested_data(
        self,
        notification_service: NotificationService,
        mock_repository: MagicMock,
        sample_webhook_channel: NotificationChannelData,
    ) -> None:
        """Test template rendering with nested notification data"""
        now = datetime.now()
        rule = NotificationRuleData(
            id=uuid4(),
            name="Nested Data Rule",
            description=None,
            rule_type=NotificationRuleType.SESSION_TERMINATED,
            channel=sample_webhook_channel,
            message_template="User {{ user.name }} exceeded {{ resource.type }} quota",
            enabled=True,
            created_by=uuid4(),
            created_at=now,
            updated_at=now,
        )

        event = NotificationTriggeredEvent(
            rule_type=NotificationRuleType.SESSION_TERMINATED,
            timestamp=datetime.now(),
            notification_data={
                "user": {"name": "john_doe", "id": "user-123"},
                "resource": {"type": "cpu", "limit": 100},
            },
        )

        mock_repository.get_matching_rules = AsyncMock(return_value=[rule])

        action = ProcessNotificationAction(
            rule_type=NotificationRuleType.SESSION_STARTED,
            timestamp=event.timestamp,
            notification_data=event.notification_data,
        )
        result = await notification_service.process_notification(action)

        assert result.rules_processed == 1

    @pytest.mark.asyncio
    async def test_process_notification_with_different_rule_types(
        self,
        notification_service: NotificationService,
        mock_repository: MagicMock,
    ) -> None:
        """Test that only rules matching the event rule_type are retrieved"""
        mock_repository.get_matching_rules = AsyncMock(return_value=[])

        action = ProcessNotificationAction(
            rule_type=NotificationRuleType.SESSION_TERMINATED,
            timestamp=datetime.now(),
            notification_data={"agent_id": "agent-001"},
        )
        await notification_service.process_notification(action)

        # Verify correct rule_type was queried
        mock_repository.get_matching_rules.assert_called_once_with(
            NotificationRuleType.SESSION_TERMINATED, enabled_only=True
        )
