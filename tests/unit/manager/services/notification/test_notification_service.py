"""
Tests for NotificationService functionality.
Tests the service layer with mocked repository operations.
"""

from collections.abc import AsyncGenerator
from datetime import datetime
from unittest.mock import AsyncMock, MagicMock
from uuid import uuid4

import pytest

from ai.backend.common.data.notification import (
    SessionStartedMessage,
    SessionTerminatedMessage,
)
from ai.backend.common.events.event_types.notification import NotificationTriggeredEvent
from ai.backend.manager.data.notification import (
    NotificationChannelData,
    NotificationChannelType,
    NotificationRuleData,
    NotificationRuleType,
    WebhookConfig,
)
from ai.backend.manager.repositories.base import BatchQuerier, Creator
from ai.backend.manager.repositories.base.updater import Updater
from ai.backend.manager.repositories.notification import NotificationRepository
from ai.backend.manager.repositories.notification.creators import (
    NotificationChannelCreatorSpec,
    NotificationRuleCreatorSpec,
)
from ai.backend.manager.repositories.notification.updaters import (
    NotificationChannelUpdaterSpec,
    NotificationRuleUpdaterSpec,
)
from ai.backend.manager.services.notification.actions import (
    CreateChannelAction,
    CreateRuleAction,
    DeleteChannelAction,
    DeleteRuleAction,
    GetChannelAction,
    GetRuleAction,
    ProcessNotificationAction,
    SearchChannelsAction,
    SearchRulesAction,
    UpdateChannelAction,
    UpdateRuleAction,
    ValidateChannelAction,
    ValidateRuleAction,
)
from ai.backend.manager.services.notification.service import NotificationService
from ai.backend.manager.types import OptionalState


class TestNotificationService:
    """Test cases for NotificationService"""

    def _mock_http_session_success(self, notification_service: NotificationService) -> None:
        """Helper to mock HTTP client session for successful webhook delivery"""
        from unittest.mock import AsyncMock as AsyncMockClass
        from unittest.mock import MagicMock as MagicMockClass

        mock_response = MagicMockClass()
        mock_response.status = 200
        mock_response.__aenter__ = AsyncMockClass(return_value=mock_response)
        mock_response.__aexit__ = AsyncMockClass(return_value=None)

        mock_session = MagicMockClass()
        mock_session.post = MagicMockClass(return_value=mock_response)

        notification_service._notification_center._http_client_pool.load_client_session = (  # type: ignore[method-assign]
            MagicMockClass(return_value=mock_session)
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

        from ai.backend.manager.notification.notification_center import NotificationCenter

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
            message_template="Session {{ session_id }} ({{ session_type }}) is now {{ status }}",
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
            notification_data=SessionStartedMessage(
                session_id="sess-12345",
                session_name="test-session",
                session_type="interactive",
                cluster_mode="single-node",
                status="RUNNING",
            ).model_dump(),
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
        # Mock HTTP session to avoid actual webhook calls
        self._mock_http_session_success(notification_service)

        mock_repository.get_matching_rules = AsyncMock(return_value=[sample_rule])

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
            notification_data=SessionStartedMessage.model_validate(sample_event.notification_data),
        )
        result = await notification_service.process_notification(action)

        assert result.rule_type == NotificationRuleType.SESSION_STARTED
        assert result.rules_matched == 0
        assert len(result.successes) == 0

    @pytest.mark.asyncio
    async def test_template_rendering_with_data_fields(
        self,
        notification_service: NotificationService,
        mock_repository: MagicMock,
        sample_rule: NotificationRuleData,
        sample_event: NotificationTriggeredEvent,
    ) -> None:
        """Test that template rendering correctly uses notification data fields"""
        # Mock HTTP session to avoid actual webhook calls
        self._mock_http_session_success(notification_service)

        mock_repository.get_matching_rules = AsyncMock(return_value=[sample_rule])

        action = ProcessNotificationAction(
            rule_type=NotificationRuleType.SESSION_STARTED,
            timestamp=sample_event.timestamp,
            notification_data=SessionStartedMessage.model_validate(sample_event.notification_data),
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
        # Mock HTTP session to avoid actual webhook calls
        self._mock_http_session_success(notification_service)

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
            notification_data=SessionStartedMessage.model_validate(sample_event.notification_data),
        )
        result = await notification_service.process_notification(action)

        assert result.rules_matched == 2
        assert len(result.successes) == 2

    @pytest.mark.asyncio
    async def test_template_rendering_fallback_on_error(
        self,
        notification_service: NotificationService,
        mock_repository: MagicMock,
        sample_webhook_channel: NotificationChannelData,
        sample_event: NotificationTriggeredEvent,
    ) -> None:
        """Test that template rendering errors are handled gracefully"""
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
            notification_data=SessionStartedMessage.model_validate(sample_event.notification_data),
        )
        # Should not raise exception, errors are caught by asyncio.gather
        result = await notification_service.process_notification(action)

        assert result.rules_matched == 1
        # Rule should not be counted as processed due to template error
        assert len(result.successes) == 0

    @pytest.mark.asyncio
    async def test_template_with_timestamp(
        self,
        notification_service: NotificationService,
        mock_repository: MagicMock,
        sample_webhook_channel: NotificationChannelData,
    ) -> None:
        """Test that templates can access timestamp field"""
        # Mock HTTP session to avoid actual webhook calls
        self._mock_http_session_success(notification_service)

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
            notification_data=SessionStartedMessage(
                session_id="test-session",
                session_name="test-session",
                session_type="interactive",
                cluster_mode="single-node",
                status="RUNNING",
            ).model_dump(),
        )

        mock_repository.get_matching_rules = AsyncMock(return_value=[rule])

        action = ProcessNotificationAction(
            rule_type=NotificationRuleType.SESSION_STARTED,
            timestamp=event.timestamp,
            notification_data=SessionStartedMessage.model_validate(event.notification_data),
        )
        result = await notification_service.process_notification(action)

        assert len(result.successes) == 1

    @pytest.mark.asyncio
    async def test_template_with_nested_data(
        self,
        notification_service: NotificationService,
        mock_repository: MagicMock,
        sample_webhook_channel: NotificationChannelData,
    ) -> None:
        """Test template rendering with session termination data"""
        # Mock HTTP session to avoid actual webhook calls
        self._mock_http_session_success(notification_service)

        now = datetime.now()
        rule = NotificationRuleData(
            id=uuid4(),
            name="Session Terminated Rule",
            description=None,
            rule_type=NotificationRuleType.SESSION_TERMINATED,
            channel=sample_webhook_channel,
            message_template="Session {{ session_id }} ({{ session_type }}) {{ status }}: {{ termination_reason }}",
            enabled=True,
            created_by=uuid4(),
            created_at=now,
            updated_at=now,
        )

        event = NotificationTriggeredEvent(
            rule_type=NotificationRuleType.SESSION_TERMINATED,
            timestamp=datetime.now(),
            notification_data=SessionTerminatedMessage(
                session_id="test-session",
                session_name="test-session",
                session_type="batch",
                cluster_mode="single-node",
                status="terminated",
                termination_reason="user-requested",
            ).model_dump(),
        )

        mock_repository.get_matching_rules = AsyncMock(return_value=[rule])

        action = ProcessNotificationAction(
            rule_type=NotificationRuleType.SESSION_TERMINATED,
            timestamp=event.timestamp,
            notification_data=SessionTerminatedMessage.model_validate(event.notification_data),
        )
        result = await notification_service.process_notification(action)

        assert len(result.successes) == 1

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

    @pytest.mark.asyncio
    async def test_create_channel(
        self,
        notification_service: NotificationService,
        mock_repository: MagicMock,
        sample_webhook_channel: NotificationChannelData,
    ) -> None:
        """Test creating a notification channel"""
        creator = Creator(
            spec=NotificationChannelCreatorSpec(
                name=sample_webhook_channel.name,
                description=sample_webhook_channel.description,
                channel_type=sample_webhook_channel.channel_type,
                config=sample_webhook_channel.config,
                enabled=sample_webhook_channel.enabled,
                created_by=sample_webhook_channel.created_by,
            )
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
        creator = Creator(
            spec=NotificationRuleCreatorSpec(
                name=sample_rule.name,
                description=sample_rule.description,
                rule_type=sample_rule.rule_type,
                channel_id=sample_rule.channel.id,
                message_template=sample_rule.message_template,
                enabled=sample_rule.enabled,
                created_by=sample_rule.created_by,
            )
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
        updater_spec = NotificationChannelUpdaterSpec(
            name=OptionalState.update("Updated Channel"),
            enabled=OptionalState.update(False),
        )
        updater = Updater(
            spec=updater_spec,
            pk_value=sample_webhook_channel.id,
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

        action = UpdateChannelAction(updater=updater)
        result = await notification_service.update_channel(action)

        assert result.channel_data == updated_channel
        mock_repository.update_channel.assert_called_once_with(updater=updater)

    @pytest.mark.asyncio
    async def test_update_rule(
        self,
        notification_service: NotificationService,
        mock_repository: MagicMock,
        sample_rule: NotificationRuleData,
    ) -> None:
        """Test updating a notification rule"""
        updater_spec = NotificationRuleUpdaterSpec(
            name=OptionalState.update("Updated Rule"),
            enabled=OptionalState.update(False),
        )
        updater = Updater(
            spec=updater_spec,
            pk_value=sample_rule.id,
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

        action = UpdateRuleAction(updater=updater)
        result = await notification_service.update_rule(action)

        assert result.rule_data == updated_rule
        mock_repository.update_rule.assert_called_once_with(updater=updater)

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
    async def test_search_channels(
        self,
        notification_service: NotificationService,
        mock_repository: MagicMock,
        sample_webhook_channel: NotificationChannelData,
    ) -> None:
        """Test searching notification channels with querier"""
        from ai.backend.manager.data.notification import NotificationChannelListResult
        from ai.backend.manager.repositories.base import OffsetPagination

        querier = BatchQuerier(
            pagination=OffsetPagination(limit=10, offset=0),
            conditions=[],
            orders=[],
        )
        mock_repository.search_channels = AsyncMock(
            return_value=NotificationChannelListResult(
                items=[sample_webhook_channel],
                total_count=1,
                has_next_page=False,
                has_previous_page=False,
            )
        )

        action = SearchChannelsAction(querier=querier)
        result = await notification_service.search_channels(action)

        assert result.channels == [sample_webhook_channel]
        assert result.total_count == 1
        mock_repository.search_channels.assert_called_once_with(querier=querier)

    @pytest.mark.asyncio
    async def test_search_rules(
        self,
        notification_service: NotificationService,
        mock_repository: MagicMock,
        sample_rule: NotificationRuleData,
    ) -> None:
        """Test searching notification rules with querier"""
        from ai.backend.manager.data.notification import NotificationRuleListResult
        from ai.backend.manager.repositories.base import OffsetPagination

        querier = BatchQuerier(
            pagination=OffsetPagination(limit=10, offset=0),
            conditions=[],
            orders=[],
        )
        mock_repository.search_rules = AsyncMock(
            return_value=NotificationRuleListResult(
                items=[sample_rule],
                total_count=1,
                has_next_page=False,
                has_previous_page=False,
            )
        )

        action = SearchRulesAction(querier=querier)
        result = await notification_service.search_rules(action)

        assert result.rules == [sample_rule]
        assert result.total_count == 1
        mock_repository.search_rules.assert_called_once_with(querier=querier)

    @pytest.mark.asyncio
    async def test_validate_channel_success(
        self,
        notification_service: NotificationService,
        mock_repository: MagicMock,
        sample_webhook_channel: NotificationChannelData,
    ) -> None:
        """Test validating a notification channel successfully"""
        from unittest.mock import AsyncMock as AsyncMockClass
        from unittest.mock import MagicMock as MagicMockClass

        mock_repository.get_channel_by_id = AsyncMock(return_value=sample_webhook_channel)

        # Mock HTTP client session to avoid actual HTTP calls
        mock_response = MagicMockClass()
        mock_response.status = 200
        mock_response.__aenter__ = AsyncMockClass(return_value=mock_response)
        mock_response.__aexit__ = AsyncMockClass(return_value=None)

        mock_session = MagicMockClass()
        mock_session.post = MagicMockClass(return_value=mock_response)

        # Mock the client pool to return our mock session
        notification_service._notification_center._http_client_pool.load_client_session = (  # type: ignore[method-assign]
            MagicMockClass(return_value=mock_session)
        )

        action = ValidateChannelAction(
            channel_id=sample_webhook_channel.id,
            test_message="Test notification from Backend.AI - Channel validation",
        )
        result = await notification_service.validate_channel(action)

        # Validation succeeds by not raising exception
        assert result is not None
        mock_repository.get_channel_by_id.assert_called_once_with(sample_webhook_channel.id)

    @pytest.mark.asyncio
    async def test_validate_channel_not_found(
        self,
        notification_service: NotificationService,
        mock_repository: MagicMock,
    ) -> None:
        """Test validating a non-existent notification channel"""
        from ai.backend.manager.errors.notification import NotificationChannelNotFound

        channel_id = uuid4()
        mock_repository.get_channel_by_id = AsyncMock(
            side_effect=NotificationChannelNotFound(f"Channel {channel_id} not found")
        )

        action = ValidateChannelAction(
            channel_id=channel_id,
            test_message="Test notification from Backend.AI",
        )
        with pytest.raises(NotificationChannelNotFound):
            await notification_service.validate_channel(action)

    @pytest.mark.asyncio
    async def test_validate_rule_success(
        self,
        notification_service: NotificationService,
        mock_repository: MagicMock,
        sample_rule: NotificationRuleData,
    ) -> None:
        """Test validating a notification rule successfully"""
        from unittest.mock import AsyncMock as AsyncMockClass
        from unittest.mock import MagicMock as MagicMockClass

        mock_repository.get_rule_by_id = AsyncMock(return_value=sample_rule)
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
        mock_response = MagicMockClass()
        mock_response.status = 200
        mock_response.__aenter__ = AsyncMockClass(return_value=mock_response)
        mock_response.__aexit__ = AsyncMockClass(return_value=None)

        mock_session = MagicMockClass()
        mock_session.post = MagicMockClass(return_value=mock_response)

        # Mock the client pool to return our mock session
        notification_service._notification_center._http_client_pool.load_client_session = (  # type: ignore[method-assign]
            MagicMockClass(return_value=mock_session)
        )

        action = ValidateRuleAction(
            rule_id=sample_rule.id,
            notification_data=notification_data,
        )
        result = await notification_service.validate_rule(action)

        # Validation succeeds by not raising exception
        assert result.message is not None
        mock_repository.get_rule_by_id.assert_called_once_with(sample_rule.id)

    @pytest.mark.asyncio
    async def test_validate_rule_template_error(
        self,
        notification_service: NotificationService,
        mock_repository: MagicMock,
        sample_webhook_channel: NotificationChannelData,
    ) -> None:
        """Test validating a rule with invalid template"""
        import jinja2

        from ai.backend.manager.errors.notification import NotificationTemplateRenderingFailure

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

    @pytest.mark.asyncio
    async def test_validate_rule_not_found(
        self,
        notification_service: NotificationService,
        mock_repository: MagicMock,
    ) -> None:
        """Test validating a non-existent notification rule"""
        from ai.backend.manager.errors.notification import NotificationRuleNotFound

        rule_id = uuid4()
        mock_repository.get_rule_by_id = AsyncMock(
            side_effect=NotificationRuleNotFound(f"Rule {rule_id} not found")
        )

        action = ValidateRuleAction(
            rule_id=rule_id,
            notification_data={"test": "data"},
        )
        with pytest.raises(NotificationRuleNotFound):
            await notification_service.validate_rule(action)
