from collections.abc import AsyncIterator, Generator
from typing import Any
from unittest.mock import AsyncMock, MagicMock, Mock, patch

import pytest
from aiohttp import web

from ai.backend.manager.api.gql.graphql_ws.handler import GraphQLTransportWSHandler
from ai.backend.manager.api.gql.graphql_ws.types import (
    ClientCompleteMessage,
    GQLWSMessageType,
    PingMessage,
    SubscribeMessage,
    SubscribePayload,
)


async def _async_iter_from(items: list[Any]) -> AsyncIterator[Any]:
    for item in items:
        yield item


class TestGraphQLTransportWSHandler:
    """Tests for the top-level WS protocol handler."""

    @pytest.fixture
    def handler(self) -> GraphQLTransportWSHandler:
        return GraphQLTransportWSHandler(
            schema=MagicMock(),
            gql_deps=MagicMock(),
            max_msg_size=4 * 1024 * 1024,
            connection_init_timeout=5.0,
        )

    @pytest.fixture
    def request_ctx(self) -> MagicMock:
        ctx = MagicMock()
        ctx.request = MagicMock(spec=web.Request)
        return ctx

    @pytest.fixture
    def mock_conn(self) -> AsyncMock:
        conn = AsyncMock()
        conn.wait_connection_init.return_value = True
        conn.sender = AsyncMock()
        conn.handler_return = MagicMock(spec=web.WebSocketResponse)
        conn.receiver.__aiter__ = lambda self: _async_iter_from([])
        return conn

    @pytest.fixture
    def mock_subs(self) -> MagicMock:
        subs = MagicMock()
        subs.start = AsyncMock()
        subs.cancel = Mock()
        subs.cancel_all = AsyncMock()
        return subs

    @pytest.fixture(autouse=True)
    def _patch_handler(self, mock_conn: AsyncMock, mock_subs: MagicMock) -> Generator[None]:
        with (
            patch(
                "ai.backend.manager.api.gql.graphql_ws.handler.GraphQLWSConnection.open",
                new_callable=AsyncMock,
                return_value=mock_conn,
            ),
            patch(
                "ai.backend.manager.api.gql.graphql_ws.handler.SubscriptionExecutor",
                return_value=mock_subs,
            ),
        ):
            yield

    async def test_handle_returns_early_on_init_failure(
        self,
        handler: GraphQLTransportWSHandler,
        request_ctx: MagicMock,
        mock_conn: AsyncMock,
    ) -> None:
        mock_conn.wait_connection_init.return_value = False

        result = await handler.handle(request_ctx)

        assert result is mock_conn.handler_return
        mock_conn.wait_connection_init.assert_awaited_once_with(wait_seconds=5.0)

    async def test_handle_dispatches_subscribe(
        self,
        handler: GraphQLTransportWSHandler,
        request_ctx: MagicMock,
        mock_conn: AsyncMock,
        mock_subs: MagicMock,
    ) -> None:
        msg = SubscribeMessage(
            type=GQLWSMessageType.SUBSCRIBE,
            id="1",
            payload=SubscribePayload(query="subscription { e }"),
        )
        mock_conn.receiver.__aiter__ = lambda self: _async_iter_from([msg])

        await handler.handle(request_ctx)

        mock_subs.start.assert_awaited_once()
        mock_subs.cancel_all.assert_awaited_once()

    async def test_handle_dispatches_complete(
        self,
        handler: GraphQLTransportWSHandler,
        request_ctx: MagicMock,
        mock_conn: AsyncMock,
        mock_subs: MagicMock,
    ) -> None:
        msg = ClientCompleteMessage(type=GQLWSMessageType.COMPLETE, id="1")
        mock_conn.receiver.__aiter__ = lambda self: _async_iter_from([msg])

        await handler.handle(request_ctx)

        mock_subs.cancel.assert_called_once()
        mock_subs.cancel_all.assert_awaited_once()

    async def test_handle_dispatches_ping(
        self,
        handler: GraphQLTransportWSHandler,
        request_ctx: MagicMock,
        mock_conn: AsyncMock,
    ) -> None:
        mock_conn.receiver.__aiter__ = lambda self: _async_iter_from([PingMessage()])

        await handler.handle(request_ctx)

        mock_conn.sender.send_pong.assert_awaited_once()

    async def test_handle_catches_exception_in_message_loop(
        self,
        handler: GraphQLTransportWSHandler,
        request_ctx: MagicMock,
        mock_conn: AsyncMock,
        mock_subs: MagicMock,
    ) -> None:
        async def _exploding_iter(_err: bool = True) -> AsyncIterator[Any]:
            if _err:
                raise RuntimeError("unexpected")
            yield

        mock_conn.receiver.__aiter__ = lambda self: _exploding_iter()

        result = await handler.handle(request_ctx)

        assert result is mock_conn.handler_return
        mock_subs.cancel_all.assert_awaited_once()
