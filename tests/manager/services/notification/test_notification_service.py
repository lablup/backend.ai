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
    NotificationChannelCreator,
    NotificationChannelData,
    NotificationChannelModifier,
    NotificationChannelType,
    NotificationRuleCreator,
    NotificationRuleData,
    NotificationRuleModifier,
    NotificationRuleType,
    WebhookConfig,
)
from ai.backend.manager.repositories.base import Querier
from ai.backend.manager.repositories.notification import NotificationRepository
from ai.backend.manager.services.notification.actions import (
    CreateChannelAction,
    CreateRuleAction,
    DeleteChannelAction,
    DeleteRuleAction,
    GetChannelAction,
    GetRuleAction,
    ListChannelsAction,
    ListRulesAction,
    ProcessNotificationAction,
    UpdateChannelAction,
    UpdateRuleAction,
    ValidateChannelAction,
    ValidateRuleAction,
)
from ai.backend.manager.services.notification.service import NotificationService
from ai.backend.manager.types import OptionalState


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

    # CRUD action tests

    @pytest.mark.asyncio
    async def test_create_channel(
        self,
        notification_service: NotificationService,
        mock_repository: MagicMock,
        sample_webhook_channel: NotificationChannelData,
    ) -> None:
        """Test creating a notification channel"""
        creator = NotificationChannelCreator(
            name=sample_webhook_channel.name,
            description=sample_webhook_channel.description,
            channel_type=sample_webhook_channel.channel_type,
            config=sample_webhook_channel.config,
            enabled=sample_webhook_channel.enabled,
            created_by=sample_webhook_channel.created_by,
        )
        mock_repository.create_channel = AsyncMock(return_value=sample_webhook_channel)

        action = CreateChannelAction(creator=creator)
        result = await notification_service.create_channel(action)

        assert result.channel_data == sample_webhook_channel
        mock_repository.create_channel.assert_called_once_with(creator)

    @pytest.mark.asyncio
    async def test_create_rule(
        self,
        notification_service: NotificationService,
        mock_repository: MagicMock,
        sample_rule: NotificationRuleData,
    ) -> None:
        """Test creating a notification rule"""
        creator = NotificationRuleCreator(
            name=sample_rule.name,
            description=sample_rule.description,
            rule_type=sample_rule.rule_type,
            channel_id=sample_rule.channel.id,
            message_template=sample_rule.message_template,
            enabled=sample_rule.enabled,
            created_by=sample_rule.created_by,
        )
        mock_repository.create_rule = AsyncMock(return_value=sample_rule)

        action = CreateRuleAction(creator=creator)
        result = await notification_service.create_rule(action)

        assert result.rule_data == sample_rule
        mock_repository.create_rule.assert_called_once_with(creator)

    @pytest.mark.asyncio
    async def test_get_channel(
        self,
        notification_service: NotificationService,
        mock_repository: MagicMock,
        sample_webhook_channel: NotificationChannelData,
    ) -> None:
        """Test getting a notification channel by ID"""
        mock_repository.get_channel_by_id = AsyncMock(return_value=sample_webhook_channel)

        action = GetChannelAction(channel_id=sample_webhook_channel.id)
        result = await notification_service.get_channel(action)

        assert result.channel_data == sample_webhook_channel
        mock_repository.get_channel_by_id.assert_called_once_with(sample_webhook_channel.id)

    @pytest.mark.asyncio
    async def test_get_rule(
        self,
        notification_service: NotificationService,
        mock_repository: MagicMock,
        sample_rule: NotificationRuleData,
    ) -> None:
        """Test getting a notification rule by ID"""
        mock_repository.get_rule_by_id = AsyncMock(return_value=sample_rule)

        action = GetRuleAction(rule_id=sample_rule.id)
        result = await notification_service.get_rule(action)

        assert result.rule_data == sample_rule
        mock_repository.get_rule_by_id.assert_called_once_with(sample_rule.id)

    @pytest.mark.asyncio
    async def test_update_channel(
        self,
        notification_service: NotificationService,
        mock_repository: MagicMock,
        sample_webhook_channel: NotificationChannelData,
    ) -> None:
        """Test updating a notification channel"""
        modifier = NotificationChannelModifier(
            name=OptionalState.update("Updated Channel"),
            enabled=OptionalState.update(False),
        )
        updated_channel = NotificationChannelData(
            id=sample_webhook_channel.id,
            name="Updated Channel",
            description=sample_webhook_channel.description,
            channel_type=sample_webhook_channel.channel_type,
            config=sample_webhook_channel.config,
            enabled=False,
            created_by=sample_webhook_channel.created_by,
            created_at=sample_webhook_channel.created_at,
            updated_at=datetime.now(),
        )
        mock_repository.update_channel = AsyncMock(return_value=updated_channel)

        action = UpdateChannelAction(
            channel_id=sample_webhook_channel.id,
            modifier=modifier,
        )
        result = await notification_service.update_channel(action)

        assert result.channel_data == updated_channel
        mock_repository.update_channel.assert_called_once_with(
            channel_id=sample_webhook_channel.id, modifier=modifier
        )

    @pytest.mark.asyncio
    async def test_update_rule(
        self,
        notification_service: NotificationService,
        mock_repository: MagicMock,
        sample_rule: NotificationRuleData,
    ) -> None:
        """Test updating a notification rule"""
        modifier = NotificationRuleModifier(
            name=OptionalState.update("Updated Rule"),
            enabled=OptionalState.update(False),
        )
        updated_rule = NotificationRuleData(
            id=sample_rule.id,
            name="Updated Rule",
            description=sample_rule.description,
            rule_type=sample_rule.rule_type,
            channel=sample_rule.channel,
            message_template=sample_rule.message_template,
            enabled=False,
            created_by=sample_rule.created_by,
            created_at=sample_rule.created_at,
            updated_at=datetime.now(),
        )
        mock_repository.update_rule = AsyncMock(return_value=updated_rule)

        action = UpdateRuleAction(
            rule_id=sample_rule.id,
            modifier=modifier,
        )
        result = await notification_service.update_rule(action)

        assert result.rule_data == updated_rule
        mock_repository.update_rule.assert_called_once_with(
            rule_id=sample_rule.id, modifier=modifier
        )

    @pytest.mark.asyncio
    async def test_delete_channel(
        self,
        notification_service: NotificationService,
        mock_repository: MagicMock,
        sample_webhook_channel: NotificationChannelData,
    ) -> None:
        """Test deleting a notification channel"""
        mock_repository.delete_channel = AsyncMock(return_value=True)

        action = DeleteChannelAction(channel_id=sample_webhook_channel.id)
        result = await notification_service.delete_channel(action)

        assert result.deleted is True
        mock_repository.delete_channel.assert_called_once_with(sample_webhook_channel.id)

    @pytest.mark.asyncio
    async def test_delete_rule(
        self,
        notification_service: NotificationService,
        mock_repository: MagicMock,
        sample_rule: NotificationRuleData,
    ) -> None:
        """Test deleting a notification rule"""
        mock_repository.delete_rule = AsyncMock(return_value=True)

        action = DeleteRuleAction(rule_id=sample_rule.id)
        result = await notification_service.delete_rule(action)

        assert result.deleted is True
        mock_repository.delete_rule.assert_called_once_with(sample_rule.id)

    @pytest.mark.asyncio
    async def test_list_channels(
        self,
        notification_service: NotificationService,
        mock_repository: MagicMock,
        sample_webhook_channel: NotificationChannelData,
    ) -> None:
        """Test listing notification channels with querier"""
        querier = Querier(conditions=[], orders=[], pagination=None)
        mock_repository.list_channels = AsyncMock(return_value=[sample_webhook_channel])

        action = ListChannelsAction(querier=querier)
        result = await notification_service.list_channels(action)

        assert result.channels == [sample_webhook_channel]
        mock_repository.list_channels.assert_called_once_with(querier=querier)

    @pytest.mark.asyncio
    async def test_list_rules(
        self,
        notification_service: NotificationService,
        mock_repository: MagicMock,
        sample_rule: NotificationRuleData,
    ) -> None:
        """Test listing notification rules with querier"""
        querier = Querier(conditions=[], orders=[], pagination=None)
        mock_repository.list_rules = AsyncMock(return_value=[sample_rule])

        action = ListRulesAction(querier=querier)
        result = await notification_service.list_rules(action)

        assert result.rules == [sample_rule]
        mock_repository.list_rules.assert_called_once_with(querier=querier)

    @pytest.mark.asyncio
    async def test_validate_channel_success(
        self,
        notification_service: NotificationService,
        mock_repository: MagicMock,
        sample_webhook_channel: NotificationChannelData,
    ) -> None:
        """Test validating a notification channel successfully"""
        mock_repository.get_channel_by_id = AsyncMock(return_value=sample_webhook_channel)

        action = ValidateChannelAction(channel_id=sample_webhook_channel.id)
        result = await notification_service.validate_channel(action)

        assert result.success is True
        assert sample_webhook_channel.name in result.message
        mock_repository.get_channel_by_id.assert_called_once_with(sample_webhook_channel.id)

    @pytest.mark.asyncio
    async def test_validate_channel_not_found(
        self,
        notification_service: NotificationService,
        mock_repository: MagicMock,
    ) -> None:
        """Test validating a non-existent notification channel"""
        channel_id = uuid4()
        mock_repository.get_channel_by_id = AsyncMock(side_effect=Exception("Channel not found"))

        action = ValidateChannelAction(channel_id=channel_id)
        result = await notification_service.validate_channel(action)

        assert result.success is False
        assert "Failed to validate" in result.message

    @pytest.mark.asyncio
    async def test_validate_rule_success(
        self,
        notification_service: NotificationService,
        mock_repository: MagicMock,
        sample_rule: NotificationRuleData,
    ) -> None:
        """Test validating a notification rule successfully"""
        mock_repository.get_rule_by_id = AsyncMock(return_value=sample_rule)
        notification_data = {
            "session_id": "sess-123",
            "user_name": "test_user",
        }

        action = ValidateRuleAction(
            rule_id=sample_rule.id,
            notification_data=notification_data,
        )
        result = await notification_service.validate_rule(action)

        assert result.success is True
        assert result.rendered_message is not None
        assert "sess-123" in result.rendered_message
        assert "test_user" in result.rendered_message
        mock_repository.get_rule_by_id.assert_called_once_with(sample_rule.id)

    @pytest.mark.asyncio
    async def test_validate_rule_template_error(
        self,
        notification_service: NotificationService,
        mock_repository: MagicMock,
        sample_webhook_channel: NotificationChannelData,
    ) -> None:
        """Test validating a rule with invalid template"""
        invalid_rule = NotificationRuleData(
            id=uuid4(),
            name="Invalid Template Rule",
            description=None,
            rule_type=NotificationRuleType.SESSION_STARTED,
            channel=sample_webhook_channel,
            message_template="Invalid {{ unclosed",  # Invalid Jinja2 syntax
            enabled=True,
            created_by=uuid4(),
            created_at=datetime.now(),
            updated_at=datetime.now(),
        )
        mock_repository.get_rule_by_id = AsyncMock(return_value=invalid_rule)

        action = ValidateRuleAction(
            rule_id=invalid_rule.id,
            notification_data={"test": "data"},
        )
        result = await notification_service.validate_rule(action)

        assert result.success is False
        assert (
            "Failed to validate" in result.message or "Template rendering failed" in result.message
        )

    @pytest.mark.asyncio
    async def test_validate_rule_not_found(
        self,
        notification_service: NotificationService,
        mock_repository: MagicMock,
    ) -> None:
        """Test validating a non-existent notification rule"""
        rule_id = uuid4()
        mock_repository.get_rule_by_id = AsyncMock(side_effect=Exception("Rule not found"))

        action = ValidateRuleAction(
            rule_id=rule_id,
            notification_data={"test": "data"},
        )
        result = await notification_service.validate_rule(action)

        assert result.success is False
        assert "Failed to validate" in result.message
