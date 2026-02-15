import uuid
from unittest.mock import AsyncMock, MagicMock

import pytest
from yarl import URL

from ai.backend.client.v2.base_client import BackendAIClient
from ai.backend.client.v2.config import ClientConfig
from ai.backend.client.v2.domains.notification import NotificationClient
from ai.backend.common.data.notification.types import (
    NotificationChannelType,
    NotificationRuleType,
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

from .conftest import MockAuth

_DEFAULT_CONFIG = ClientConfig(endpoint=URL("https://api.example.com"))

_CHANNEL_ID = uuid.UUID("aaaaaaaa-aaaa-aaaa-aaaa-aaaaaaaaaaaa")
_RULE_ID = uuid.UUID("bbbbbbbb-bbbb-bbbb-bbbb-bbbbbbbbbbbb")
_USER_ID = uuid.UUID("cccccccc-cccc-cccc-cccc-cccccccccccc")


def _make_client(mock_session: MagicMock | None = None) -> BackendAIClient:
    return BackendAIClient(
        _DEFAULT_CONFIG,
        MockAuth(),
        mock_session or MagicMock(),
    )


def _make_request_session(resp: AsyncMock) -> MagicMock:
    mock_ctx = AsyncMock()
    mock_ctx.__aenter__ = AsyncMock(return_value=resp)
    mock_ctx.__aexit__ = AsyncMock(return_value=False)
    mock_session = MagicMock()
    mock_session.request = MagicMock(return_value=mock_ctx)
    return mock_session


def _ok_response(data: dict[str, object]) -> AsyncMock:
    resp = AsyncMock()
    resp.status = 200
    resp.json = AsyncMock(return_value=data)
    return resp


def _channel_dto_data() -> dict[str, object]:
    return {
        "id": str(_CHANNEL_ID),
        "name": "test-channel",
        "description": "Test channel",
        "channel_type": "webhook",
        "spec": {"url": "https://example.com/webhook"},
        "enabled": True,
        "created_at": "2025-01-01T00:00:00",
        "created_by": str(_USER_ID),
        "updated_at": "2025-01-01T00:00:00",
    }


def _rule_dto_data() -> dict[str, object]:
    return {
        "id": str(_RULE_ID),
        "name": "test-rule",
        "description": "Test rule",
        "rule_type": "session.started",
        "channel": _channel_dto_data(),
        "message_template": "Session {{ session_id }} started",
        "enabled": True,
        "created_at": "2025-01-01T00:00:00",
        "created_by": str(_USER_ID),
        "updated_at": "2025-01-01T00:00:00",
    }


class TestNotificationClientChannels:
    @pytest.mark.asyncio
    async def test_create_channel(self) -> None:
        mock_resp = _ok_response({"channel": _channel_dto_data()})
        mock_session = _make_request_session(mock_resp)
        client = _make_client(mock_session)
        notification_client = NotificationClient(client)

        request = CreateNotificationChannelRequest(
            name="test-channel",
            channel_type=NotificationChannelType.WEBHOOK,
            spec=WebhookSpec(url="https://example.com/webhook"),
        )
        result = await notification_client.create_channel(request)

        assert isinstance(result, CreateNotificationChannelResponse)
        call_args = mock_session.request.call_args
        assert call_args[0][0] == "POST"
        assert "/notifications/channels" in str(call_args[0][1])
        assert call_args.kwargs["json"]["name"] == "test-channel"
        assert call_args.kwargs["json"]["channel_type"] == "webhook"

    @pytest.mark.asyncio
    async def test_search_channels(self) -> None:
        mock_resp = _ok_response({
            "channels": [_channel_dto_data()],
            "pagination": {"total": 1, "offset": 0, "limit": 50},
        })
        mock_session = _make_request_session(mock_resp)
        client = _make_client(mock_session)
        notification_client = NotificationClient(client)

        request = SearchNotificationChannelsRequest(limit=50, offset=0)
        result = await notification_client.search_channels(request)

        assert isinstance(result, ListNotificationChannelsResponse)
        assert len(result.channels) == 1
        call_args = mock_session.request.call_args
        assert call_args[0][0] == "POST"
        assert "/notifications/channels/search" in str(call_args[0][1])

    @pytest.mark.asyncio
    async def test_get_channel(self) -> None:
        mock_resp = _ok_response({"channel": _channel_dto_data()})
        mock_session = _make_request_session(mock_resp)
        client = _make_client(mock_session)
        notification_client = NotificationClient(client)

        result = await notification_client.get_channel(_CHANNEL_ID)

        assert isinstance(result, GetNotificationChannelResponse)
        assert result.channel.name == "test-channel"
        call_args = mock_session.request.call_args
        assert call_args[0][0] == "GET"
        assert f"/notifications/channels/{_CHANNEL_ID}" in str(call_args[0][1])
        assert call_args.kwargs["json"] is None

    @pytest.mark.asyncio
    async def test_update_channel(self) -> None:
        mock_resp = _ok_response({"channel": _channel_dto_data()})
        mock_session = _make_request_session(mock_resp)
        client = _make_client(mock_session)
        notification_client = NotificationClient(client)

        request = UpdateNotificationChannelRequest(name="updated-channel")
        result = await notification_client.update_channel(_CHANNEL_ID, request)

        assert isinstance(result, UpdateNotificationChannelResponse)
        call_args = mock_session.request.call_args
        assert call_args[0][0] == "PATCH"
        assert f"/notifications/channels/{_CHANNEL_ID}" in str(call_args[0][1])
        assert call_args.kwargs["json"]["name"] == "updated-channel"

    @pytest.mark.asyncio
    async def test_delete_channel(self) -> None:
        mock_resp = _ok_response({"deleted": True})
        mock_session = _make_request_session(mock_resp)
        client = _make_client(mock_session)
        notification_client = NotificationClient(client)

        result = await notification_client.delete_channel(_CHANNEL_ID)

        assert isinstance(result, DeleteNotificationChannelResponse)
        assert result.deleted is True
        call_args = mock_session.request.call_args
        assert call_args[0][0] == "DELETE"
        assert f"/notifications/channels/{_CHANNEL_ID}" in str(call_args[0][1])

    @pytest.mark.asyncio
    async def test_validate_channel(self) -> None:
        mock_resp = _ok_response({"channel_id": str(_CHANNEL_ID)})
        mock_session = _make_request_session(mock_resp)
        client = _make_client(mock_session)
        notification_client = NotificationClient(client)

        request = ValidateNotificationChannelRequest(test_message="Hello test")
        result = await notification_client.validate_channel(_CHANNEL_ID, request)

        assert isinstance(result, ValidateNotificationChannelResponse)
        assert result.channel_id == _CHANNEL_ID
        call_args = mock_session.request.call_args
        assert call_args[0][0] == "POST"
        assert f"/notifications/channels/{_CHANNEL_ID}/validate" in str(call_args[0][1])
        assert call_args.kwargs["json"]["test_message"] == "Hello test"


class TestNotificationClientRules:
    @pytest.mark.asyncio
    async def test_list_rule_types(self) -> None:
        mock_resp = _ok_response({
            "rule_types": ["session.started", "session.terminated"],
        })
        mock_session = _make_request_session(mock_resp)
        client = _make_client(mock_session)
        notification_client = NotificationClient(client)

        result = await notification_client.list_rule_types()

        assert isinstance(result, ListNotificationRuleTypesResponse)
        assert len(result.rule_types) == 2
        call_args = mock_session.request.call_args
        assert call_args[0][0] == "GET"
        assert "/notifications/rule-types" in str(call_args[0][1])
        assert call_args.kwargs["json"] is None

    @pytest.mark.asyncio
    async def test_get_rule_type_schema(self) -> None:
        mock_resp = _ok_response({
            "rule_type": "session.started",
            "json_schema": {"type": "object", "properties": {}},
        })
        mock_session = _make_request_session(mock_resp)
        client = _make_client(mock_session)
        notification_client = NotificationClient(client)

        result = await notification_client.get_rule_type_schema(
            NotificationRuleType.SESSION_STARTED,
        )

        assert isinstance(result, NotificationRuleTypeSchemaResponse)
        assert result.rule_type == NotificationRuleType.SESSION_STARTED
        assert result.json_schema == {"type": "object", "properties": {}}
        call_args = mock_session.request.call_args
        assert call_args[0][0] == "GET"
        assert "/notifications/rule-types/session.started/schema" in str(call_args[0][1])

    @pytest.mark.asyncio
    async def test_create_rule(self) -> None:
        mock_resp = _ok_response({"rule": _rule_dto_data()})
        mock_session = _make_request_session(mock_resp)
        client = _make_client(mock_session)
        notification_client = NotificationClient(client)

        request = CreateNotificationRuleRequest(
            name="test-rule",
            rule_type=NotificationRuleType.SESSION_STARTED,
            channel_id=_CHANNEL_ID,
            message_template="Session {{ session_id }} started",
        )
        result = await notification_client.create_rule(request)

        assert isinstance(result, CreateNotificationRuleResponse)
        call_args = mock_session.request.call_args
        assert call_args[0][0] == "POST"
        assert "/notifications/rules" in str(call_args[0][1])
        assert call_args.kwargs["json"]["name"] == "test-rule"
        assert call_args.kwargs["json"]["rule_type"] == "session.started"

    @pytest.mark.asyncio
    async def test_search_rules(self) -> None:
        mock_resp = _ok_response({
            "rules": [_rule_dto_data()],
            "pagination": {"total": 1, "offset": 0, "limit": 50},
        })
        mock_session = _make_request_session(mock_resp)
        client = _make_client(mock_session)
        notification_client = NotificationClient(client)

        request = SearchNotificationRulesRequest(limit=50, offset=0)
        result = await notification_client.search_rules(request)

        assert isinstance(result, ListNotificationRulesResponse)
        assert len(result.rules) == 1
        call_args = mock_session.request.call_args
        assert call_args[0][0] == "POST"
        assert "/notifications/rules/search" in str(call_args[0][1])

    @pytest.mark.asyncio
    async def test_get_rule(self) -> None:
        mock_resp = _ok_response({"rule": _rule_dto_data()})
        mock_session = _make_request_session(mock_resp)
        client = _make_client(mock_session)
        notification_client = NotificationClient(client)

        result = await notification_client.get_rule(_RULE_ID)

        assert isinstance(result, GetNotificationRuleResponse)
        assert result.rule.name == "test-rule"
        call_args = mock_session.request.call_args
        assert call_args[0][0] == "GET"
        assert f"/notifications/rules/{_RULE_ID}" in str(call_args[0][1])
        assert call_args.kwargs["json"] is None

    @pytest.mark.asyncio
    async def test_update_rule(self) -> None:
        mock_resp = _ok_response({"rule": _rule_dto_data()})
        mock_session = _make_request_session(mock_resp)
        client = _make_client(mock_session)
        notification_client = NotificationClient(client)

        request = UpdateNotificationRuleRequest(name="updated-rule")
        result = await notification_client.update_rule(_RULE_ID, request)

        assert isinstance(result, UpdateNotificationRuleResponse)
        call_args = mock_session.request.call_args
        assert call_args[0][0] == "PATCH"
        assert f"/notifications/rules/{_RULE_ID}" in str(call_args[0][1])
        assert call_args.kwargs["json"]["name"] == "updated-rule"

    @pytest.mark.asyncio
    async def test_delete_rule(self) -> None:
        mock_resp = _ok_response({"deleted": True})
        mock_session = _make_request_session(mock_resp)
        client = _make_client(mock_session)
        notification_client = NotificationClient(client)

        result = await notification_client.delete_rule(_RULE_ID)

        assert isinstance(result, DeleteNotificationRuleResponse)
        assert result.deleted is True
        call_args = mock_session.request.call_args
        assert call_args[0][0] == "DELETE"
        assert f"/notifications/rules/{_RULE_ID}" in str(call_args[0][1])

    @pytest.mark.asyncio
    async def test_validate_rule(self) -> None:
        mock_resp = _ok_response({"message": "Session abc123 started"})
        mock_session = _make_request_session(mock_resp)
        client = _make_client(mock_session)
        notification_client = NotificationClient(client)

        request = ValidateNotificationRuleRequest(
            notification_data={"session_id": "abc123"},
        )
        result = await notification_client.validate_rule(_RULE_ID, request)

        assert isinstance(result, ValidateNotificationRuleResponse)
        assert result.message == "Session abc123 started"
        call_args = mock_session.request.call_args
        assert call_args[0][0] == "POST"
        assert f"/notifications/rules/{_RULE_ID}/validate" in str(call_args[0][1])
        assert call_args.kwargs["json"]["notification_data"] == {"session_id": "abc123"}
