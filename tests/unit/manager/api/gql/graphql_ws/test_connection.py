from collections.abc import AsyncIterator
from typing import Any
from unittest.mock import AsyncMock, MagicMock, PropertyMock, patch

import pytest
from aiohttp import WSMsgType

from ai.backend.manager.api.gql.graphql_ws.connection import (
    GraphQLWSConnection,
    WSReceiver,
    WSSender,
)
from ai.backend.manager.api.gql.graphql_ws.types import GQLWSMessageType

# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------


def _make_ws_msg(*, msg_type: WSMsgType, data: dict[str, Any] | None = None) -> MagicMock:
    """Create a mock aiohttp WSMessage."""
    msg = MagicMock()
    msg.type = msg_type
    if data is not None:
        msg.json.return_value = data
    return msg


def _make_mock_ws(*, closed: bool = False) -> AsyncMock:
    """Create a mock ``web.WebSocketResponse``."""
    ws = AsyncMock()
    type(ws).closed = PropertyMock(return_value=closed)
    return ws


# ===========================================================================
# WSReceiver
# ===========================================================================


class TestWSReceiver:
    """Tests for the read-side WebSocket view."""

    @pytest.fixture
    def mock_ws(self) -> AsyncMock:
        return _make_mock_ws()

    @pytest.fixture
    def receiver(self, mock_ws: AsyncMock) -> WSReceiver:
        return WSReceiver(mock_ws)

    # -- receive_init -------------------------------------------------------

    async def test_receive_init_success(self, receiver: WSReceiver, mock_ws: AsyncMock) -> None:
        mock_ws.receive.return_value = _make_ws_msg(
            msg_type=WSMsgType.TEXT,
            data={"type": GQLWSMessageType.CONNECTION_INIT},
        )
        assert await receiver.receive_init(wait_seconds=5.0) is True

    async def test_receive_init_wrong_type(self, receiver: WSReceiver, mock_ws: AsyncMock) -> None:
        mock_ws.receive.return_value = _make_ws_msg(
            msg_type=WSMsgType.TEXT,
            data={"type": "subscribe"},
        )
        assert await receiver.receive_init(wait_seconds=5.0) is False

    async def test_receive_init_binary_message(
        self, receiver: WSReceiver, mock_ws: AsyncMock
    ) -> None:
        mock_ws.receive.return_value = _make_ws_msg(msg_type=WSMsgType.BINARY)
        assert await receiver.receive_init(wait_seconds=5.0) is False

    async def test_receive_init_timeout(self, receiver: WSReceiver, mock_ws: AsyncMock) -> None:
        mock_ws.receive.side_effect = TimeoutError
        assert await receiver.receive_init(wait_seconds=0.01) is False

    # -- __aiter__ ----------------------------------------------------------

    async def test_aiter_yields_valid_messages(
        self, receiver: WSReceiver, mock_ws: AsyncMock
    ) -> None:
        subscribe_msg = _make_ws_msg(
            msg_type=WSMsgType.TEXT,
            data={"type": "subscribe", "id": "1", "payload": {"query": "{ e }"}},
        )
        ping_msg = _make_ws_msg(msg_type=WSMsgType.TEXT, data={"type": "ping"})
        close_msg = _make_ws_msg(msg_type=WSMsgType.CLOSE)

        mock_ws.__aiter__ = lambda self: _async_iter_from([subscribe_msg, ping_msg, close_msg])

        messages: list[Any] = []
        async for m in receiver:
            messages.append(m)
        assert len(messages) == 2

    async def test_aiter_skips_malformed_messages(
        self, receiver: WSReceiver, mock_ws: AsyncMock
    ) -> None:
        bad_msg = _make_ws_msg(
            msg_type=WSMsgType.TEXT,
            data={"type": "unknown_garbage"},
        )
        good_msg = _make_ws_msg(
            msg_type=WSMsgType.TEXT,
            data={"type": "ping"},
        )
        close_msg = _make_ws_msg(msg_type=WSMsgType.CLOSE)

        mock_ws.__aiter__ = lambda self: _async_iter_from([bad_msg, good_msg, close_msg])

        messages: list[Any] = []
        async for m in receiver:
            messages.append(m)
        assert len(messages) == 1

    async def test_aiter_stops_on_error(self, receiver: WSReceiver, mock_ws: AsyncMock) -> None:
        error_msg = _make_ws_msg(msg_type=WSMsgType.ERROR)

        mock_ws.__aiter__ = lambda self: _async_iter_from([error_msg])

        messages: list[Any] = []
        async for m in receiver:
            messages.append(m)
        assert len(messages) == 0


# ===========================================================================
# WSSender
# ===========================================================================


class TestWSSender:
    """Tests for the write-side WebSocket view."""

    @pytest.fixture
    def mock_ws(self) -> AsyncMock:
        return _make_mock_ws()

    @pytest.fixture
    def sender(self, mock_ws: AsyncMock) -> WSSender:
        return WSSender(mock_ws)

    # -- send methods -------------------------------------------------------

    async def test_send_ack(self, sender: WSSender, mock_ws: AsyncMock) -> None:
        await sender.send_ack()
        mock_ws.send_json.assert_awaited_once()
        payload = mock_ws.send_json.call_args[0][0]
        assert payload["type"] == GQLWSMessageType.CONNECTION_ACK

    async def test_send_next(self, sender: WSSender, mock_ws: AsyncMock) -> None:
        result = MagicMock()
        result.data = {"count": 42}
        result.errors = None

        await sender.send_next("sub-1", result)
        payload = mock_ws.send_json.call_args[0][0]
        assert payload["type"] == GQLWSMessageType.NEXT
        assert payload["id"] == "sub-1"
        assert payload["payload"]["data"] == {"count": 42}

    async def test_send_next_with_errors(self, sender: WSSender, mock_ws: AsyncMock) -> None:
        error = MagicMock()
        error.formatted = {"message": "field error", "locations": []}
        result = MagicMock()
        result.data = None
        result.errors = [error]

        await sender.send_next("sub-1", result)
        payload = mock_ws.send_json.call_args[0][0]
        assert payload["payload"]["errors"] == [{"message": "field error", "locations": []}]

    async def test_send_pre_execution_error(self, sender: WSSender, mock_ws: AsyncMock) -> None:
        gql_err = MagicMock()
        gql_err.formatted = {"message": "syntax error"}
        error = MagicMock()
        error.errors = [gql_err]

        await sender.send_pre_execution_error("sub-1", error)
        payload = mock_ws.send_json.call_args[0][0]
        assert payload["type"] == GQLWSMessageType.ERROR
        assert payload["id"] == "sub-1"
        assert payload["payload"] == [{"message": "syntax error"}]

    async def test_send_internal_error(self, sender: WSSender, mock_ws: AsyncMock) -> None:
        await sender.send_internal_error("sub-1")
        payload = mock_ws.send_json.call_args[0][0]
        assert payload["type"] == GQLWSMessageType.ERROR
        assert payload["payload"] == [{"message": "Internal server error"}]

    async def test_send_complete(self, sender: WSSender, mock_ws: AsyncMock) -> None:
        await sender.send_complete("sub-1")
        payload = mock_ws.send_json.call_args[0][0]
        assert payload["type"] == GQLWSMessageType.COMPLETE
        assert payload["id"] == "sub-1"

    async def test_send_pong(self, sender: WSSender, mock_ws: AsyncMock) -> None:
        await sender.send_pong()
        payload = mock_ws.send_json.call_args[0][0]
        assert payload["type"] == GQLWSMessageType.PONG

    # -- close methods ------------------------------------------------------

    async def test_close(self, sender: WSSender, mock_ws: AsyncMock) -> None:
        await sender.close()
        mock_ws.close.assert_awaited_once()

    async def test_close_skipped_when_already_closed(self, sender: WSSender) -> None:
        closed_ws = _make_mock_ws(closed=True)
        s = WSSender(closed_ws)
        await s.close()
        closed_ws.close.assert_not_awaited()

    async def test_close_init_timeout(self, sender: WSSender, mock_ws: AsyncMock) -> None:
        await sender.close_init_timeout()
        mock_ws.close.assert_awaited_once_with(
            code=4408, message=b"Connection initialisation timeout"
        )

    async def test_close_unauthorized(self, sender: WSSender, mock_ws: AsyncMock) -> None:
        await sender.close_unauthorized()
        mock_ws.close.assert_awaited_once_with(code=4401, message=b"Unauthorized")

    async def test_close_duplicate_subscriber(self, sender: WSSender, mock_ws: AsyncMock) -> None:
        await sender.close_duplicate_subscriber()
        mock_ws.close.assert_awaited_once_with(code=4409, message=b"Subscriber already exists")


# ===========================================================================
# GraphQLWSConnection
# ===========================================================================


class TestGraphQLWSConnection:
    """Tests for the connection lifecycle wrapper."""

    @pytest.fixture
    def mock_ws(self) -> AsyncMock:
        return _make_mock_ws()

    @pytest.fixture
    def conn(self, mock_ws: AsyncMock) -> GraphQLWSConnection:
        return GraphQLWSConnection(mock_ws)

    async def test_wait_connection_init_success(self, conn: GraphQLWSConnection) -> None:
        with patch.object(conn.receiver, "receive_init", new_callable=AsyncMock) as recv_init:
            recv_init.return_value = True
            with patch.object(conn.sender, "send_ack", new_callable=AsyncMock) as send_ack:
                result = await conn.wait_connection_init(wait_seconds=5.0)
                assert result is True
                recv_init.assert_awaited_once_with(wait_seconds=5.0)
                send_ack.assert_awaited_once()

    async def test_wait_connection_init_timeout(self, conn: GraphQLWSConnection) -> None:
        with patch.object(conn.receiver, "receive_init", new_callable=AsyncMock) as recv_init:
            recv_init.return_value = False
            with patch.object(
                conn.sender, "close_init_timeout", new_callable=AsyncMock
            ) as close_timeout:
                result = await conn.wait_connection_init(wait_seconds=1.0)
                assert result is False
                close_timeout.assert_awaited_once()

    async def test_wait_connection_init_exception(self, conn: GraphQLWSConnection) -> None:
        with patch.object(conn.receiver, "receive_init", new_callable=AsyncMock) as recv_init:
            recv_init.side_effect = RuntimeError("boom")
            with patch.object(conn.sender, "close", new_callable=AsyncMock) as close:
                result = await conn.wait_connection_init(wait_seconds=1.0)
                assert result is False
                close.assert_awaited_once()

    def test_handler_return(self, conn: GraphQLWSConnection, mock_ws: AsyncMock) -> None:
        assert conn.handler_return is mock_ws


# ---------------------------------------------------------------------------
# Async iteration helper
# ---------------------------------------------------------------------------


async def _async_iter_from(items: list[Any]) -> AsyncIterator[Any]:
    for item in items:
        yield item
