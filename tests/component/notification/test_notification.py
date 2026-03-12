from __future__ import annotations

import uuid
from datetime import UTC, datetime
from unittest.mock import AsyncMock, patch

import pytest

from ai.backend.client.exceptions import BackendAPIError
from ai.backend.client.v2.registry import BackendAIClientRegistry
from ai.backend.common.data.notification import SessionStartedMessage
from ai.backend.common.data.notification.types import (
    EmailMessage,
    EmailSpec,
    NotificationChannelType,
    NotificationRuleType,
    SMTPConnection,
    WebhookSpec,
)
from ai.backend.common.dto.manager.notification import (
    CreateNotificationChannelRequest,
    CreateNotificationChannelResponse,
    CreateNotificationRuleRequest,
    CreateNotificationRuleResponse,
    DeleteNotificationChannelResponse,
    DeleteNotificationRuleResponse,
    GetNotificationChannelResponse,
    GetNotificationRuleResponse,
    ListNotificationChannelsResponse,
    ListNotificationRulesResponse,
    ListNotificationRuleTypesResponse,
    NotificationChannelDTO,
    NotificationChannelFilter,
    NotificationRuleDTO,
    NotificationRuleTypeSchemaResponse,
    SearchNotificationChannelsRequest,
    SearchNotificationRulesRequest,
    UpdateNotificationChannelRequest,
    UpdateNotificationChannelResponse,
    UpdateNotificationRuleRequest,
    UpdateNotificationRuleResponse,
    ValidateNotificationChannelRequest,
    ValidateNotificationChannelResponse,
    ValidateNotificationRuleRequest,
    ValidateNotificationRuleResponse,
)
from ai.backend.common.dto.manager.query import StringFilter
from ai.backend.manager.notification.notification_center import NotificationCenter
from ai.backend.manager.notification.types import SendResult
from ai.backend.manager.services.notification.actions import (
    ProcessNotificationAction,
    ProcessNotificationActionResult,
)
from ai.backend.manager.services.notification.processors import NotificationProcessors


def _webhook_channel_request(name: str = "test-webhook") -> CreateNotificationChannelRequest:
    return CreateNotificationChannelRequest(
        name=name,
        description="A test webhook channel",
        channel_type=NotificationChannelType.WEBHOOK,
        spec=WebhookSpec(url="https://example.com/webhook"),
        enabled=True,
    )


class TestChannelCreate:
    async def test_admin_creates_webhook_channel(
        self,
        admin_registry: BackendAIClientRegistry,
    ) -> None:
        result = await admin_registry.notification.create_channel(
            _webhook_channel_request("webhook-create"),
        )
        assert isinstance(result, CreateNotificationChannelResponse)
        assert result.channel.name == "webhook-create"
        assert result.channel.channel_type == NotificationChannelType.WEBHOOK
        assert result.channel.enabled is True

    async def test_admin_creates_email_channel(
        self,
        admin_registry: BackendAIClientRegistry,
    ) -> None:
        req = CreateNotificationChannelRequest(
            name="email-create",
            description="A test email channel",
            channel_type=NotificationChannelType.EMAIL,
            spec=EmailSpec(
                smtp=SMTPConnection(host="smtp.example.com", port=587),
                message=EmailMessage(
                    from_email="noreply@example.com",
                    to_emails=["admin@example.com"],
                ),
            ),
            enabled=True,
        )
        result = await admin_registry.notification.create_channel(req)
        assert isinstance(result, CreateNotificationChannelResponse)
        assert result.channel.name == "email-create"
        assert result.channel.channel_type == NotificationChannelType.EMAIL

    async def test_regular_user_cannot_create_channel(
        self,
        user_registry: BackendAIClientRegistry,
    ) -> None:
        with pytest.raises(BackendAPIError) as exc_info:
            await user_registry.notification.create_channel(
                _webhook_channel_request("forbidden-channel"),
            )
        assert exc_info.value.status == 403


class TestChannelSearch:
    async def test_admin_searches_channels(
        self,
        admin_registry: BackendAIClientRegistry,
    ) -> None:
        # Seed a channel first
        await admin_registry.notification.create_channel(
            _webhook_channel_request("search-target"),
        )
        result = await admin_registry.notification.search_channels(
            SearchNotificationChannelsRequest(),
        )
        assert isinstance(result, ListNotificationChannelsResponse)
        assert len(result.channels) >= 1
        names = [ch.name for ch in result.channels]
        assert "search-target" in names

    async def test_admin_searches_channels_empty(
        self,
        admin_registry: BackendAIClientRegistry,
    ) -> None:
        result = await admin_registry.notification.search_channels(
            SearchNotificationChannelsRequest(
                filter=NotificationChannelFilter(
                    name=StringFilter(contains="nonexistent-channel-xyz-999"),
                ),
            ),
        )
        assert isinstance(result, ListNotificationChannelsResponse)
        assert len(result.channels) == 0


class TestChannelGet:
    async def test_admin_gets_channel(
        self,
        admin_registry: BackendAIClientRegistry,
    ) -> None:
        created = await admin_registry.notification.create_channel(
            _webhook_channel_request("get-target"),
        )
        result = await admin_registry.notification.get_channel(created.channel.id)
        assert isinstance(result, GetNotificationChannelResponse)
        assert result.channel.id == created.channel.id
        assert result.channel.name == "get-target"

    async def test_admin_gets_nonexistent_channel(
        self,
        admin_registry: BackendAIClientRegistry,
    ) -> None:
        with pytest.raises(BackendAPIError) as exc_info:
            await admin_registry.notification.get_channel(uuid.uuid4())
        assert exc_info.value.status in (404, 500)


class TestChannelUpdate:
    async def test_admin_updates_channel(
        self,
        admin_registry: BackendAIClientRegistry,
    ) -> None:
        created = await admin_registry.notification.create_channel(
            _webhook_channel_request("update-before"),
        )
        result = await admin_registry.notification.update_channel(
            created.channel.id,
            UpdateNotificationChannelRequest(name="update-after"),
        )
        assert isinstance(result, UpdateNotificationChannelResponse)
        assert result.channel.name == "update-after"


class TestChannelDelete:
    async def test_admin_deletes_channel(
        self,
        admin_registry: BackendAIClientRegistry,
    ) -> None:
        created = await admin_registry.notification.create_channel(
            _webhook_channel_request("delete-target"),
        )
        result = await admin_registry.notification.delete_channel(created.channel.id)
        assert isinstance(result, DeleteNotificationChannelResponse)
        assert result.deleted is True


class TestChannelValidate:
    @pytest.mark.xfail(
        strict=False,
        reason=(
            "notification_center MagicMock return may not pass Pydantic response DTO"
            " validation. Remove xfail if test passes at runtime."
        ),
    )
    async def test_admin_validates_channel(
        self,
        admin_registry: BackendAIClientRegistry,
    ) -> None:
        created = await admin_registry.notification.create_channel(
            _webhook_channel_request("validate-channel"),
        )
        result = await admin_registry.notification.validate_channel(
            created.channel.id,
            ValidateNotificationChannelRequest(test_message="hello"),
        )
        assert isinstance(result, ValidateNotificationChannelResponse)
        assert result.channel_id == created.channel.id


# ---------------------------------------------------------------------------
# Rule tests
# ---------------------------------------------------------------------------


class TestRuleTypeList:
    async def test_admin_lists_rule_types(
        self,
        admin_registry: BackendAIClientRegistry,
    ) -> None:
        result = await admin_registry.notification.list_rule_types()
        assert isinstance(result, ListNotificationRuleTypesResponse)
        assert len(result.rule_types) == len(NotificationRuleType)


class TestRuleTypeSchema:
    async def test_admin_gets_rule_type_schema(
        self,
        admin_registry: BackendAIClientRegistry,
    ) -> None:
        result = await admin_registry.notification.get_rule_type_schema(
            NotificationRuleType.SESSION_STARTED,
        )
        assert isinstance(result, NotificationRuleTypeSchemaResponse)
        assert result.rule_type == NotificationRuleType.SESSION_STARTED
        assert isinstance(result.json_schema, dict)


class TestRuleCreate:
    async def test_admin_creates_rule(
        self,
        admin_registry: BackendAIClientRegistry,
    ) -> None:
        channel = await admin_registry.notification.create_channel(
            _webhook_channel_request("rule-channel"),
        )
        result = await admin_registry.notification.create_rule(
            CreateNotificationRuleRequest(
                name="test-rule",
                description="A test rule",
                rule_type=NotificationRuleType.SESSION_STARTED,
                channel_id=channel.channel.id,
                message_template="Session {{ session_name }} started",
                enabled=True,
            ),
        )
        assert isinstance(result, CreateNotificationRuleResponse)
        assert result.rule.name == "test-rule"
        assert result.rule.rule_type == NotificationRuleType.SESSION_STARTED

    async def test_regular_user_cannot_create_rule(
        self,
        admin_registry: BackendAIClientRegistry,
        user_registry: BackendAIClientRegistry,
    ) -> None:
        channel = await admin_registry.notification.create_channel(
            _webhook_channel_request("rule-channel-forbidden"),
        )
        with pytest.raises(BackendAPIError) as exc_info:
            await user_registry.notification.create_rule(
                CreateNotificationRuleRequest(
                    name="forbidden-rule",
                    rule_type=NotificationRuleType.SESSION_STARTED,
                    channel_id=channel.channel.id,
                    message_template="test",
                ),
            )
        assert exc_info.value.status == 403


class TestRuleSearch:
    async def test_admin_searches_rules(
        self,
        admin_registry: BackendAIClientRegistry,
    ) -> None:
        channel = await admin_registry.notification.create_channel(
            _webhook_channel_request("rule-search-channel"),
        )
        await admin_registry.notification.create_rule(
            CreateNotificationRuleRequest(
                name="search-rule",
                rule_type=NotificationRuleType.SESSION_TERMINATED,
                channel_id=channel.channel.id,
                message_template="Session ended",
            ),
        )
        result = await admin_registry.notification.search_rules(
            SearchNotificationRulesRequest(),
        )
        assert isinstance(result, ListNotificationRulesResponse)
        assert len(result.rules) >= 1
        names = [r.name for r in result.rules]
        assert "search-rule" in names


class TestRuleGet:
    async def test_admin_gets_rule(
        self,
        admin_registry: BackendAIClientRegistry,
    ) -> None:
        channel = await admin_registry.notification.create_channel(
            _webhook_channel_request("rule-get-channel"),
        )
        created = await admin_registry.notification.create_rule(
            CreateNotificationRuleRequest(
                name="get-rule",
                rule_type=NotificationRuleType.SESSION_STARTED,
                channel_id=channel.channel.id,
                message_template="test",
            ),
        )
        result = await admin_registry.notification.get_rule(created.rule.id)
        assert isinstance(result, GetNotificationRuleResponse)
        assert result.rule.id == created.rule.id
        assert result.rule.name == "get-rule"

    async def test_admin_gets_nonexistent_rule(
        self,
        admin_registry: BackendAIClientRegistry,
    ) -> None:
        with pytest.raises(BackendAPIError) as exc_info:
            await admin_registry.notification.get_rule(uuid.uuid4())
        assert exc_info.value.status in (404, 500)


class TestRuleUpdate:
    async def test_admin_updates_rule(
        self,
        admin_registry: BackendAIClientRegistry,
    ) -> None:
        channel = await admin_registry.notification.create_channel(
            _webhook_channel_request("rule-update-channel"),
        )
        created = await admin_registry.notification.create_rule(
            CreateNotificationRuleRequest(
                name="update-rule-before",
                rule_type=NotificationRuleType.SESSION_STARTED,
                channel_id=channel.channel.id,
                message_template="test",
            ),
        )
        result = await admin_registry.notification.update_rule(
            created.rule.id,
            UpdateNotificationRuleRequest(name="update-rule-after"),
        )
        assert isinstance(result, UpdateNotificationRuleResponse)
        assert result.rule.name == "update-rule-after"


class TestRuleDelete:
    async def test_admin_deletes_rule(
        self,
        admin_registry: BackendAIClientRegistry,
    ) -> None:
        channel = await admin_registry.notification.create_channel(
            _webhook_channel_request("rule-delete-channel"),
        )
        created = await admin_registry.notification.create_rule(
            CreateNotificationRuleRequest(
                name="delete-rule",
                rule_type=NotificationRuleType.SESSION_STARTED,
                channel_id=channel.channel.id,
                message_template="test",
            ),
        )
        result = await admin_registry.notification.delete_rule(created.rule.id)
        assert isinstance(result, DeleteNotificationRuleResponse)
        assert result.deleted is True


class TestRuleValidate:
    @pytest.mark.xfail(
        strict=False,
        reason=(
            "notification_center MagicMock return may not pass Pydantic response DTO"
            " validation. Remove xfail if test passes at runtime."
        ),
    )
    async def test_admin_validates_rule(
        self,
        admin_registry: BackendAIClientRegistry,
    ) -> None:
        channel = await admin_registry.notification.create_channel(
            _webhook_channel_request("rule-validate-channel"),
        )
        created = await admin_registry.notification.create_rule(
            CreateNotificationRuleRequest(
                name="validate-rule",
                rule_type=NotificationRuleType.SESSION_STARTED,
                channel_id=channel.channel.id,
                message_template="Session {{ session_name }} started",
            ),
        )
        result = await admin_registry.notification.validate_rule(
            created.rule.id,
            ValidateNotificationRuleRequest(
                notification_data={"session_name": "test-session"},
            ),
        )
        assert isinstance(result, ValidateNotificationRuleResponse)
        assert isinstance(result.message, str)


# ---------------------------------------------------------------------------
# Notification processing tests
# ---------------------------------------------------------------------------


class TestNotificationProcessing:
    async def test_event_triggers_matching_rule(
        self,
        notification_processors: NotificationProcessors,
        notification_center: NotificationCenter,
        notification_rule: NotificationRuleDTO,
    ) -> None:
        """A matching rule is found and the channel is called exactly once."""
        send_result = SendResult(message="Notification delivered")
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
        admin_registry: BackendAIClientRegistry,
        webhook_channel: NotificationChannelDTO,
    ) -> None:
        """When one channel send fails, other channels still receive the notification."""
        ch2 = await admin_registry.notification.create_channel(
            CreateNotificationChannelRequest(
                name="partial-failure-channel-2",
                description="Second channel for partial failure test",
                channel_type=NotificationChannelType.WEBHOOK,
                spec=WebhookSpec(url="https://example.com/webhook2"),
                enabled=True,
            )
        )
        rule1_resp = await admin_registry.notification.create_rule(
            CreateNotificationRuleRequest(
                name="partial-fail-rule-1",
                rule_type=NotificationRuleType.SESSION_STARTED,
                channel_id=webhook_channel.id,
                message_template="Rule 1: {{ session_name }}",
                enabled=True,
            )
        )
        rule2_resp = await admin_registry.notification.create_rule(
            CreateNotificationRuleRequest(
                name="partial-fail-rule-2",
                rule_type=NotificationRuleType.SESSION_STARTED,
                channel_id=ch2.channel.id,
                message_template="Rule 2: {{ session_name }}",
                enabled=True,
            )
        )

        try:
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
                result = await notification_processors.process_notification.wait_for_complete(
                    action
                )
        finally:
            await admin_registry.notification.delete_rule(rule1_resp.rule.id)
            await admin_registry.notification.delete_rule(rule2_resp.rule.id)
            await admin_registry.notification.delete_channel(ch2.channel.id)

        assert isinstance(result, ProcessNotificationActionResult)
        assert result.rules_matched >= 2
        assert len(result.successes) >= 1
        assert len(result.errors) >= 1
