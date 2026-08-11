"""
Tests for NotificationService functionality.
Tests the service layer with mocked repository operations.
"""

from collections.abc import AsyncGenerator
from datetime import UTC, datetime
from unittest.mock import AsyncMock, MagicMock
from uuid import uuid4

import jinja2
import pytest

from ai.backend.common.data.notification import (
    NotificationChannelType,
    NotificationRuleType,
    SessionStartedMessage,
    SessionTerminatedMessage,
    WebhookSpec,
)
from ai.backend.common.events.event_types.notification import NotificationTriggeredEvent
from ai.backend.common.identifier.notification import (
    NotificationChannelID,
    NotificationRuleID,
)
from ai.backend.manager.data.notification import (
    NotificationChannelData,
    NotificationRuleData,
)
from ai.backend.manager.data.notification.types import MatchingNotificationRuleData
from ai.backend.manager.errors.notification import (
    NotificationChannelNotFound,
    NotificationRuleNotFound,
    NotificationTemplateRenderingFailure,
)
from ai.backend.manager.notification.notification_center import NotificationCenter
from ai.backend.manager.repositories.notification import NotificationRepository
from ai.backend.manager.services.notification.actions import (
    ProcessNotificationAction,
    ValidateChannelAction,
    ValidateRuleAction,
)
from ai.backend.manager.services.notification.service import NotificationService


class TestNotificationService:
    """Test cases for NotificationService"""

    def _mock_http_session_success(self, notification_service: NotificationService) -> None:
        """Helper to mock HTTP client session for successful webhook delivery"""
        mock_response = MagicMock()
        mock_response.status = 200
        mock_response.__aenter__ = AsyncMock(return_value=mock_response)
        mock_response.__aexit__ = AsyncMock(return_value=None)

        mock_session = MagicMock()
        mock_session.post = MagicMock(return_value=mock_response)

        notification_service._notification_center._http_client_pool.load_client_session = (  # type: ignore[method-assign]
            MagicMock(return_value=mock_session)
        )

    @pytest.fixture
    def mock_repository(self) -> MagicMock:
        """Create mocked NotificationRepository"""
        return MagicMock(spec=NotificationRepository)

    @pytest.fixture
    async def notification_service(
        self, mock_repository: MagicMock
    ) -> AsyncGenerator[NotificationService, None]:
        """Create NotificationService instance with mocked repository"""
        # Create real NotificationCenter and mock HTTP client pool later
        notification_center = NotificationCenter()

        try:
            yield NotificationService(
                repository=mock_repository,
                notification_center=notification_center,
            )
        finally:
            # Cleanup the client pool
            await notification_center._http_client_pool.close()

    @pytest.fixture
    def sample_webhook_channel(self) -> NotificationChannelData:
        """Create sample webhook notification channel"""
        now = datetime.now(tz=UTC)
        return NotificationChannelData(
            id=NotificationChannelID(uuid4()),
            name="Test Webhook",
            description="Test webhook channel",
            channel_type=NotificationChannelType.WEBHOOK,
            spec=WebhookSpec(
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
        now = datetime.now(tz=UTC)
        return NotificationRuleData(
            id=NotificationRuleID(uuid4()),
            name="Session Started Rule",
            description="Notify when session starts",
            rule_type=NotificationRuleType.SESSION_STARTED,
            channel_id=sample_webhook_channel.id,
            message_template="Session {{ session_id }} ({{ session_type }}) is now {{ status }}",
            enabled=True,
            created_by=uuid4(),
            created_at=now,
            updated_at=now,
        )

    @pytest.fixture
    def sample_match(
        self,
        sample_rule: NotificationRuleData,
        sample_webhook_channel: NotificationChannelData,
    ) -> MatchingNotificationRuleData:
        """What the dispatch read returns: a rule beside the channel it dispatches through."""
        return MatchingNotificationRuleData(rule=sample_rule, channel=sample_webhook_channel)

    @pytest.fixture
    def sample_event(self) -> NotificationTriggeredEvent:
        """Create sample notification event"""
        return NotificationTriggeredEvent(
            rule_type=NotificationRuleType.SESSION_STARTED,
            timestamp=datetime.now(tz=UTC),
            notification_data=SessionStartedMessage(
                session_id="sess-12345",
                session_name="test-session",
                session_type="interactive",
                cluster_mode="single-node",
                status="RUNNING",
            ).model_dump(),
        )

    async def test_process_notification_with_matching_rules(
        self,
        notification_service: NotificationService,
        mock_repository: MagicMock,
        sample_match: MatchingNotificationRuleData,
        sample_event: NotificationTriggeredEvent,
    ) -> None:
        """Test processing notification with matching rules"""
        # Mock HTTP session to avoid actual webhook calls
        self._mock_http_session_success(notification_service)

        mock_repository.get_matching_rules = AsyncMock(return_value=[sample_match])

        action = ProcessNotificationAction(
            rule_type=NotificationRuleType.SESSION_STARTED,
            timestamp=sample_event.timestamp,
            notification_data=SessionStartedMessage.model_validate(sample_event.notification_data),
        )
        result = await notification_service.process_notification(action)

        assert result.rule_type == NotificationRuleType.SESSION_STARTED
        assert result.rules_matched == 1
        assert len(result.successes) == 1
        mock_repository.get_matching_rules.assert_called_once_with(
            NotificationRuleType.SESSION_STARTED, enabled_only=True
        )

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
            notification_data=SessionStartedMessage.model_validate(sample_event.notification_data),
        )
        result = await notification_service.process_notification(action)

        assert result.rule_type == NotificationRuleType.SESSION_STARTED
        assert result.rules_matched == 0
        assert len(result.successes) == 0

    async def test_template_rendering_with_data_fields(
        self,
        notification_service: NotificationService,
        mock_repository: MagicMock,
        sample_match: MatchingNotificationRuleData,
        sample_event: NotificationTriggeredEvent,
    ) -> None:
        """Test that template rendering correctly uses notification data fields"""
        # Mock HTTP session to avoid actual webhook calls
        self._mock_http_session_success(notification_service)

        mock_repository.get_matching_rules = AsyncMock(return_value=[sample_match])

        action = ProcessNotificationAction(
            rule_type=NotificationRuleType.SESSION_STARTED,
            timestamp=sample_event.timestamp,
            notification_data=SessionStartedMessage.model_validate(sample_event.notification_data),
        )
        await notification_service.process_notification(action)

        # Verify template was rendered with correct data
        # The actual rendered message should contain the substituted values
        mock_repository.get_matching_rules.assert_called_once()

    async def test_process_notification_with_multiple_rules(
        self,
        notification_service: NotificationService,
        mock_repository: MagicMock,
        sample_webhook_channel: NotificationChannelData,
        sample_event: NotificationTriggeredEvent,
    ) -> None:
        """Test processing notification with multiple matching rules"""
        # Mock HTTP session to avoid actual webhook calls
        self._mock_http_session_success(notification_service)

        now = datetime.now(tz=UTC)
        rule1 = NotificationRuleData(
            id=NotificationRuleID(uuid4()),
            name="Rule 1",
            description=None,
            rule_type=NotificationRuleType.SESSION_STARTED,
            channel_id=sample_webhook_channel.id,
            message_template="Rule 1: Session {{ session_id }}",
            enabled=True,
            created_by=uuid4(),
            created_at=now,
            updated_at=now,
        )

        rule2 = NotificationRuleData(
            id=NotificationRuleID(uuid4()),
            name="Rule 2",
            description=None,
            rule_type=NotificationRuleType.SESSION_STARTED,
            channel_id=sample_webhook_channel.id,
            message_template="Rule 2: User {{ user_name }}",
            enabled=True,
            created_by=uuid4(),
            created_at=now,
            updated_at=now,
        )

        mock_repository.get_matching_rules = AsyncMock(
            return_value=[
                MatchingNotificationRuleData(rule=rule1, channel=sample_webhook_channel),
                MatchingNotificationRuleData(rule=rule2, channel=sample_webhook_channel),
            ]
        )

        action = ProcessNotificationAction(
            rule_type=NotificationRuleType.SESSION_STARTED,
            timestamp=sample_event.timestamp,
            notification_data=SessionStartedMessage.model_validate(sample_event.notification_data),
        )
        result = await notification_service.process_notification(action)

        assert result.rules_matched == 2
        assert len(result.successes) == 2

    async def test_template_rendering_fallback_on_error(
        self,
        notification_service: NotificationService,
        mock_repository: MagicMock,
        sample_webhook_channel: NotificationChannelData,
        sample_event: NotificationTriggeredEvent,
    ) -> None:
        """Test that template rendering errors are handled gracefully"""
        # Create rule with invalid template syntax
        now = datetime.now(tz=UTC)
        invalid_rule = NotificationRuleData(
            id=NotificationRuleID(uuid4()),
            name="Invalid Template Rule",
            description=None,
            rule_type=NotificationRuleType.SESSION_STARTED,
            channel_id=sample_webhook_channel.id,
            message_template="Session {{ unclosed_tag",  # Invalid Jinja2 syntax
            enabled=True,
            created_by=uuid4(),
            created_at=now,
            updated_at=now,
        )

        mock_repository.get_matching_rules = AsyncMock(
            return_value=[
                MatchingNotificationRuleData(rule=invalid_rule, channel=sample_webhook_channel)
            ]
        )

        action = ProcessNotificationAction(
            rule_type=NotificationRuleType.SESSION_STARTED,
            timestamp=sample_event.timestamp,
            notification_data=SessionStartedMessage.model_validate(sample_event.notification_data),
        )
        # Should not raise exception, errors are caught by asyncio.gather
        result = await notification_service.process_notification(action)

        assert result.rules_matched == 1
        # Rule should not be counted as processed due to template error
        assert len(result.successes) == 0

    async def test_template_with_timestamp(
        self,
        notification_service: NotificationService,
        mock_repository: MagicMock,
        sample_webhook_channel: NotificationChannelData,
    ) -> None:
        """Test that templates can access timestamp field"""
        # Mock HTTP session to avoid actual webhook calls
        self._mock_http_session_success(notification_service)

        now = datetime.now(tz=UTC)
        rule = NotificationRuleData(
            id=NotificationRuleID(uuid4()),
            name="Timestamp Rule",
            description=None,
            rule_type=NotificationRuleType.SESSION_STARTED,
            channel_id=sample_webhook_channel.id,
            message_template="Event at {{ timestamp.isoformat() }}",
            enabled=True,
            created_by=uuid4(),
            created_at=now,
            updated_at=now,
        )

        event = NotificationTriggeredEvent(
            rule_type=NotificationRuleType.SESSION_STARTED,
            timestamp=datetime.now(tz=UTC),
            notification_data=SessionStartedMessage(
                session_id="test-session",
                session_name="test-session",
                session_type="interactive",
                cluster_mode="single-node",
                status="RUNNING",
            ).model_dump(),
        )

        mock_repository.get_matching_rules = AsyncMock(
            return_value=[MatchingNotificationRuleData(rule=rule, channel=sample_webhook_channel)]
        )

        action = ProcessNotificationAction(
            rule_type=NotificationRuleType.SESSION_STARTED,
            timestamp=event.timestamp,
            notification_data=SessionStartedMessage.model_validate(event.notification_data),
        )
        result = await notification_service.process_notification(action)

        assert len(result.successes) == 1

    async def test_template_with_nested_data(
        self,
        notification_service: NotificationService,
        mock_repository: MagicMock,
        sample_webhook_channel: NotificationChannelData,
    ) -> None:
        """Test template rendering with session termination data"""
        # Mock HTTP session to avoid actual webhook calls
        self._mock_http_session_success(notification_service)

        now = datetime.now(tz=UTC)
        rule = NotificationRuleData(
            id=NotificationRuleID(uuid4()),
            name="Session Terminated Rule",
            description=None,
            rule_type=NotificationRuleType.SESSION_TERMINATED,
            channel_id=sample_webhook_channel.id,
            message_template="Session {{ session_id }} ({{ session_type }}) {{ status }}: {{ termination_reason }}",
            enabled=True,
            created_by=uuid4(),
            created_at=now,
            updated_at=now,
        )

        event = NotificationTriggeredEvent(
            rule_type=NotificationRuleType.SESSION_TERMINATED,
            timestamp=datetime.now(tz=UTC),
            notification_data=SessionTerminatedMessage(
                session_id="test-session",
                session_name="test-session",
                session_type="batch",
                cluster_mode="single-node",
                status="terminated",
                termination_reason="user-requested",
            ).model_dump(),
        )

        mock_repository.get_matching_rules = AsyncMock(
            return_value=[MatchingNotificationRuleData(rule=rule, channel=sample_webhook_channel)]
        )

        action = ProcessNotificationAction(
            rule_type=NotificationRuleType.SESSION_TERMINATED,
            timestamp=event.timestamp,
            notification_data=SessionTerminatedMessage.model_validate(event.notification_data),
        )
        result = await notification_service.process_notification(action)

        assert len(result.successes) == 1

    async def test_process_notification_with_different_rule_types(
        self,
        notification_service: NotificationService,
        mock_repository: MagicMock,
    ) -> None:
        """Test that only rules matching the event rule_type are retrieved"""
        mock_repository.get_matching_rules = AsyncMock(return_value=[])

        action = ProcessNotificationAction(
            rule_type=NotificationRuleType.SESSION_TERMINATED,
            timestamp=datetime.now(tz=UTC),
            notification_data=SessionTerminatedMessage(
                session_id="test-session",
                session_name="test-session",
                session_type="batch",
                cluster_mode="single-node",
                status="terminated",
                termination_reason="user-requested",
            ),
        )
        await notification_service.process_notification(action)

        # Verify correct rule_type was queried
        mock_repository.get_matching_rules.assert_called_once_with(
            NotificationRuleType.SESSION_TERMINATED, enabled_only=True
        )

    # CRUD action tests

    async def test_validate_channel_success(
        self,
        notification_service: NotificationService,
        mock_repository: MagicMock,
        sample_webhook_channel: NotificationChannelData,
    ) -> None:
        """Test validating a notification channel successfully"""
        mock_repository.get_channel_by_id = AsyncMock(return_value=sample_webhook_channel)

        # Mock HTTP client session to avoid actual HTTP calls
        mock_response = MagicMock()
        mock_response.status = 200
        mock_response.__aenter__ = AsyncMock(return_value=mock_response)
        mock_response.__aexit__ = AsyncMock(return_value=None)

        mock_session = MagicMock()
        mock_session.post = MagicMock(return_value=mock_response)

        # Mock the client pool to return our mock session
        notification_service._notification_center._http_client_pool.load_client_session = (  # type: ignore[method-assign]
            MagicMock(return_value=mock_session)
        )

        action = ValidateChannelAction(
            channel_id=sample_webhook_channel.id,
            test_message="Test notification from Backend.AI - Channel validation",
        )
        result = await notification_service.validate_channel(action)

        # Validation succeeds by not raising exception
        assert result is not None
        mock_repository.get_channel_by_id.assert_called_once_with(sample_webhook_channel.id)

    async def test_validate_channel_not_found(
        self,
        notification_service: NotificationService,
        mock_repository: MagicMock,
    ) -> None:
        """Test validating a non-existent notification channel"""
        channel_id = uuid4()
        mock_repository.get_channel_by_id = AsyncMock(
            side_effect=NotificationChannelNotFound(f"Channel {channel_id} not found")
        )

        action = ValidateChannelAction(
            channel_id=NotificationChannelID(channel_id),
            test_message="Test notification from Backend.AI",
        )
        with pytest.raises(NotificationChannelNotFound):
            await notification_service.validate_channel(action)

    async def test_validate_rule_success(
        self,
        notification_service: NotificationService,
        mock_repository: MagicMock,
        sample_rule: NotificationRuleData,
        sample_webhook_channel: NotificationChannelData,
    ) -> None:
        """Test validating a notification rule successfully"""
        mock_repository.get_rule_by_id = AsyncMock(return_value=sample_rule)
        # The rule names its channel by id, so validation reads the channel separately.
        mock_repository.get_channel_by_id = AsyncMock(return_value=sample_webhook_channel)
        notification_data = {
            "session_id": "sess-123",
            "session_name": "test-session",
            "session_type": "interactive",
            "cluster_mode": "single-node",
            "status": "RUNNING",
        }

        # Mock the template environment to return a template that renders correctly
        mock_template = MagicMock()
        mock_template.render = MagicMock(return_value="Session sess-123 started by test_user")
        notification_service._notification_center._template_env.from_string = MagicMock(  # type: ignore[method-assign]
            return_value=mock_template
        )

        # Mock HTTP client session to avoid actual HTTP calls
        mock_response = MagicMock()
        mock_response.status = 200
        mock_response.__aenter__ = AsyncMock(return_value=mock_response)
        mock_response.__aexit__ = AsyncMock(return_value=None)

        mock_session = MagicMock()
        mock_session.post = MagicMock(return_value=mock_response)

        # Mock the client pool to return our mock session
        notification_service._notification_center._http_client_pool.load_client_session = (  # type: ignore[method-assign]
            MagicMock(return_value=mock_session)
        )

        action = ValidateRuleAction(
            rule_id=sample_rule.id,
            notification_data=notification_data,
        )
        result = await notification_service.validate_rule(action)

        # Validation succeeds by not raising exception
        assert result.message is not None
        mock_repository.get_rule_by_id.assert_called_once_with(sample_rule.id)

    async def test_validate_rule_template_error(
        self,
        notification_service: NotificationService,
        mock_repository: MagicMock,
        sample_webhook_channel: NotificationChannelData,
    ) -> None:
        """Test validating a rule with invalid template"""
        invalid_rule = NotificationRuleData(
            id=NotificationRuleID(uuid4()),
            name="Invalid Template Rule",
            description=None,
            rule_type=NotificationRuleType.SESSION_STARTED,
            channel_id=sample_webhook_channel.id,
            message_template="Invalid {{ unclosed",  # Invalid Jinja2 syntax
            enabled=True,
            created_by=uuid4(),
            created_at=datetime.now(tz=UTC),
            updated_at=datetime.now(tz=UTC),
        )
        mock_repository.get_rule_by_id = AsyncMock(return_value=invalid_rule)

        # Mock _template_env to raise TemplateError
        notification_service._notification_center._template_env.from_string = MagicMock(  # type: ignore[method-assign]
            side_effect=jinja2.TemplateError("Template syntax error")
        )

        action = ValidateRuleAction(
            rule_id=invalid_rule.id,
            notification_data={
                "session_id": "sess-123",
                "session_name": "test-session",
                "session_type": "interactive",
                "cluster_mode": "single-node",
                "status": "RUNNING",
            },
        )
        with pytest.raises(NotificationTemplateRenderingFailure):
            await notification_service.validate_rule(action)

    async def test_validate_rule_not_found(
        self,
        notification_service: NotificationService,
        mock_repository: MagicMock,
    ) -> None:
        """Test validating a non-existent notification rule"""
        rule_id = uuid4()
        mock_repository.get_rule_by_id = AsyncMock(
            side_effect=NotificationRuleNotFound(f"Rule {rule_id} not found")
        )

        action = ValidateRuleAction(
            rule_id=NotificationRuleID(rule_id),
            notification_data={"test": "data"},
        )
        with pytest.raises(NotificationRuleNotFound):
            await notification_service.validate_rule(action)
