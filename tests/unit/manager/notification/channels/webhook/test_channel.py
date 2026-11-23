from __future__ import annotations

from types import TracebackType
from unittest.mock import MagicMock

import aiohttp
import pytest

from ai.backend.common.clients.http_client import ClientPool
from ai.backend.common.data.notification.types import WebhookSpec
from ai.backend.manager.errors.notification import (
    NotificationDeliveryFailure,
    WebhookConnectionFailure,
)
from ai.backend.manager.notification.channels.webhook.channel import WebhookChannel
from ai.backend.manager.notification.types import NotificationMessage


class _FakeResponse:
    status: int
    _text: str

    def __init__(self, status: int, text: str = "") -> None:
        self.status = status
        self._text = text

    async def text(self) -> str:
        return self._text


class _FakePostContext:
    _outcome: _FakeResponse | BaseException

    def __init__(self, outcome: _FakeResponse | BaseException) -> None:
        self._outcome = outcome

    async def __aenter__(self) -> _FakeResponse:
        if isinstance(self._outcome, BaseException):
            raise self._outcome
        return self._outcome

    async def __aexit__(
        self,
        exc_type: type[BaseException] | None,
        exc: BaseException | None,
        tb: TracebackType | None,
    ) -> None:
        return None


class _FakeSession:
    _outcome: _FakeResponse | BaseException

    def __init__(self, outcome: _FakeResponse | BaseException) -> None:
        self._outcome = outcome

    def post(self, *args: object, **kwargs: object) -> _FakePostContext:
        return _FakePostContext(self._outcome)


@pytest.fixture
def message() -> NotificationMessage:
    return NotificationMessage(message="test message")


@pytest.fixture
def outcome() -> _FakeResponse | BaseException:
    return _FakeResponse(200)


@pytest.fixture
def channel(outcome: _FakeResponse | BaseException) -> WebhookChannel:
    pool = MagicMock(spec=ClientPool)
    pool.load_client_session.return_value = _FakeSession(outcome)
    return WebhookChannel(pool, WebhookSpec(url="https://example.com/webhook"))


class TestWebhookChannelSend:
    @pytest.mark.parametrize(
        "outcome",
        [aiohttp.ClientConnectionError("Connection refused"), TimeoutError()],
        ids=["connection-error", "timeout"],
    )
    async def test_a_connection_failure_raises_a_webhook_connection_failure(
        self,
        channel: WebhookChannel,
        message: NotificationMessage,
        outcome: BaseException,
    ) -> None:
        with pytest.raises(WebhookConnectionFailure) as exc_info:
            await channel.send(message)

        assert exc_info.value.__cause__ is outcome

    @pytest.mark.parametrize("outcome", [_FakeResponse(500, "boom")], ids=["status-500"])
    async def test_a_failed_response_status_is_a_client_visible_delivery_failure(
        self,
        channel: WebhookChannel,
        message: NotificationMessage,
    ) -> None:
        with pytest.raises(NotificationDeliveryFailure, match="status 500: boom") as exc_info:
            await channel.send(message)

        assert exc_info.value.is_client_error()

    async def test_a_success_status_returns_a_result(
        self,
        channel: WebhookChannel,
        message: NotificationMessage,
    ) -> None:
        result = await channel.send(message)

        assert "status: 200" in result.message
