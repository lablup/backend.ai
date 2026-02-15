from __future__ import annotations

from collections.abc import AsyncIterator
from unittest.mock import AsyncMock, MagicMock, PropertyMock
from uuid import UUID

import aiohttp
import pytest
from yarl import URL

from ai.backend.client.v2.base_client import BackendAIClient
from ai.backend.client.v2.config import ClientConfig
from ai.backend.client.v2.domains.streaming import StreamingClient
from ai.backend.client.v2.streaming_types import SSEConnection, WebSocketSession
from ai.backend.common.dto.manager.streaming import (
    GetStreamAppsResponse,
    StreamProxyParams,
)

from .conftest import MockAuth

_DEFAULT_CONFIG = ClientConfig(endpoint=URL("https://api.example.com"))


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------


def _make_request_session(resp: AsyncMock) -> MagicMock:
    mock_ctx = AsyncMock()
    mock_ctx.__aenter__ = AsyncMock(return_value=resp)
    mock_ctx.__aexit__ = AsyncMock(return_value=False)
    mock_session = MagicMock()
    mock_session.request = MagicMock(return_value=mock_ctx)
    return mock_session


def _make_client(mock_session: MagicMock) -> BackendAIClient:
    return BackendAIClient(_DEFAULT_CONFIG, MockAuth(), mock_session)


def _make_streaming_client(mock_session: MagicMock) -> StreamingClient:
    return StreamingClient(_make_client(mock_session))


def _make_mock_ws(*, closed: bool = False) -> MagicMock:
    ws = MagicMock(spec=aiohttp.ClientWebSocketResponse)
    type(ws).closed = PropertyMock(return_value=closed)
    ws.send_str = AsyncMock()
    ws.send_bytes = AsyncMock()
    ws.send_json = AsyncMock()
    ws.receive_str = AsyncMock(return_value="hello")
    ws.receive_bytes = AsyncMock(return_value=b"bytes")
    ws.receive_json = AsyncMock(return_value={"key": "value"})
    ws.close = AsyncMock()
    return ws


def _make_sse_response(lines: list[bytes]) -> AsyncMock:
    line_iter = iter(lines)

    async def _readline() -> bytes:
        try:
            return next(line_iter)
        except StopIteration:
            return b""

    mock_resp = AsyncMock(spec=aiohttp.ClientResponse)
    mock_resp.status = 200
    mock_resp.reason = "OK"
    mock_resp.content = MagicMock()
    mock_resp.content.readline = _readline
    mock_resp.close = MagicMock()
    return mock_resp


# ===========================================================================
# WebSocket — Terminal PTY
# ===========================================================================


class TestConnectTerminal:
    @pytest.mark.asyncio
    async def test_opens_pty_websocket(self) -> None:
        mock_ws = _make_mock_ws()
        mock_session = MagicMock()
        mock_session.ws_connect = AsyncMock(return_value=mock_ws)
        client = _make_streaming_client(mock_session)

        async with client.connect_terminal("my-session") as ws:
            assert isinstance(ws, WebSocketSession)
            assert not ws.closed

        call_args = mock_session.ws_connect.call_args
        url = str(call_args[0][0])
        assert "/stream/session/my-session/pty" in url

    @pytest.mark.asyncio
    async def test_send_receive(self) -> None:
        mock_ws = _make_mock_ws()
        mock_session = MagicMock()
        mock_session.ws_connect = AsyncMock(return_value=mock_ws)
        client = _make_streaming_client(mock_session)

        async with client.connect_terminal("sess") as ws:
            await ws.send_str('{"type":"stdin","chars":"ls\\n"}')
            result = await ws.receive_str()
            assert result == "hello"

        mock_ws.send_str.assert_awaited_once()

    @pytest.mark.asyncio
    async def test_async_iteration(self) -> None:
        mock_ws = _make_mock_ws()
        msg1 = MagicMock(spec=aiohttp.WSMessage)
        msg1.data = '{"type":"out","data":"aGVsbG8="}'
        msg2 = MagicMock(spec=aiohttp.WSMessage)
        msg2.data = '{"type":"out","data":"d29ybGQ="}'

        async def _aiter() -> AsyncIterator[aiohttp.WSMessage]:
            for m in [msg1, msg2]:
                yield m

        mock_ws.__aiter__ = lambda self: _aiter()

        mock_session = MagicMock()
        mock_session.ws_connect = AsyncMock(return_value=mock_ws)
        client = _make_streaming_client(mock_session)

        collected = []
        async with client.connect_terminal("sess") as ws:
            async for msg in ws:
                collected.append(msg.data)
        assert len(collected) == 2


# ===========================================================================
# WebSocket — Code execution
# ===========================================================================


class TestConnectExecute:
    @pytest.mark.asyncio
    async def test_opens_execute_websocket(self) -> None:
        mock_ws = _make_mock_ws()
        mock_session = MagicMock()
        mock_session.ws_connect = AsyncMock(return_value=mock_ws)
        client = _make_streaming_client(mock_session)

        async with client.connect_execute("my-session") as ws:
            assert isinstance(ws, WebSocketSession)

        url = str(mock_session.ws_connect.call_args[0][0])
        assert "/stream/session/my-session/execute" in url

    @pytest.mark.asyncio
    async def test_send_execute_request(self) -> None:
        mock_ws = _make_mock_ws()
        mock_session = MagicMock()
        mock_session.ws_connect = AsyncMock(return_value=mock_ws)
        client = _make_streaming_client(mock_session)

        async with client.connect_execute("sess") as ws:
            await ws.send_json({"mode": "query", "code": "print(1)"})

        mock_ws.send_json.assert_awaited_once_with({"mode": "query", "code": "print(1)"})


# ===========================================================================
# WebSocket — HTTP proxy
# ===========================================================================


class TestConnectHttpProxy:
    @pytest.mark.asyncio
    async def test_opens_httpproxy_websocket_with_params(self) -> None:
        mock_ws = _make_mock_ws()
        mock_session = MagicMock()
        mock_session.ws_connect = AsyncMock(return_value=mock_ws)
        client = _make_streaming_client(mock_session)

        params = StreamProxyParams(app="jupyter", port=8080)
        async with client.connect_http_proxy("my-session", params) as ws:
            assert isinstance(ws, WebSocketSession)

        call_kwargs = mock_session.ws_connect.call_args.kwargs
        url = str(mock_session.ws_connect.call_args[0][0])
        assert "/stream/session/my-session/httpproxy" in url
        assert call_kwargs["params"]["app"] == "jupyter"
        assert call_kwargs["params"]["port"] == "8080"

    @pytest.mark.asyncio
    async def test_excludes_none_params(self) -> None:
        mock_ws = _make_mock_ws()
        mock_session = MagicMock()
        mock_session.ws_connect = AsyncMock(return_value=mock_ws)
        client = _make_streaming_client(mock_session)

        params = StreamProxyParams(app="ttyd")
        async with client.connect_http_proxy("sess", params):
            pass

        call_kwargs = mock_session.ws_connect.call_args.kwargs
        assert "port" not in call_kwargs["params"]
        assert "envs" not in call_kwargs["params"]


# ===========================================================================
# WebSocket — TCP proxy
# ===========================================================================


class TestConnectTcpProxy:
    @pytest.mark.asyncio
    async def test_opens_tcpproxy_websocket(self) -> None:
        mock_ws = _make_mock_ws()
        mock_session = MagicMock()
        mock_session.ws_connect = AsyncMock(return_value=mock_ws)
        client = _make_streaming_client(mock_session)

        params = StreamProxyParams(app="vnc")
        async with client.connect_tcp_proxy("my-session", params) as ws:
            assert isinstance(ws, WebSocketSession)

        url = str(mock_session.ws_connect.call_args[0][0])
        assert "/stream/session/my-session/tcpproxy" in url


# ===========================================================================
# SSE — Session events
# ===========================================================================


class TestSubscribeSessionEvents:
    @pytest.mark.asyncio
    async def test_opens_sse_with_default_params(self) -> None:
        mock_resp = _make_sse_response([
            b"event: session_started\n",
            b"data: {}\n",
            b"\n",
            b"",
        ])
        mock_session = MagicMock()
        mock_session.get = AsyncMock(return_value=mock_resp)
        client = _make_streaming_client(mock_session)

        async with client.subscribe_session_events() as sse:
            assert isinstance(sse, SSEConnection)
            events = []
            async for event in sse:
                events.append(event)

        assert len(events) == 1
        assert events[0].event == "session_started"

        call_kwargs = mock_session.get.call_args.kwargs
        assert call_kwargs["params"]["name"] == "*"
        assert call_kwargs["params"]["group"] == "*"
        assert call_kwargs["params"]["scope"] == "*"

    @pytest.mark.asyncio
    async def test_passes_custom_params(self) -> None:
        mock_resp = _make_sse_response([b""])
        mock_session = MagicMock()
        mock_session.get = AsyncMock(return_value=mock_resp)
        client = _make_streaming_client(mock_session)

        session_id = UUID("12345678-1234-5678-1234-567812345678")
        async with client.subscribe_session_events(
            session_name="my-sess",
            owner_access_key="AKTEST",
            session_id=session_id,
            group_name="research",
            scope="session,kernel",
        ) as sse:
            async for _ in sse:
                pass

        call_kwargs = mock_session.get.call_args.kwargs
        assert call_kwargs["params"]["name"] == "my-sess"
        assert call_kwargs["params"]["ownerAccessKey"] == "AKTEST"
        assert call_kwargs["params"]["sessionId"] == str(session_id)
        assert call_kwargs["params"]["group"] == "research"
        assert call_kwargs["params"]["scope"] == "session,kernel"

    @pytest.mark.asyncio
    async def test_iterates_multiple_events(self) -> None:
        mock_resp = _make_sse_response([
            b"event: session_enqueued\n",
            b'data: {"session_id": "abc"}\n',
            b"\n",
            b"event: session_started\n",
            b'data: {"session_id": "abc"}\n',
            b"\n",
            b"",
        ])
        mock_session = MagicMock()
        mock_session.get = AsyncMock(return_value=mock_resp)
        client = _make_streaming_client(mock_session)

        events = []
        async with client.subscribe_session_events() as sse:
            async for event in sse:
                events.append(event)

        assert len(events) == 2
        assert events[0].event == "session_enqueued"
        assert events[1].event == "session_started"


# ===========================================================================
# SSE — Background task events
# ===========================================================================


class TestSubscribeBackgroundTaskEvents:
    @pytest.mark.asyncio
    async def test_opens_sse_with_task_id(self) -> None:
        mock_resp = _make_sse_response([
            b"event: bgtask_updated\n",
            b'data: {"task_id": "t1", "current_progress": 50}\n',
            b"\n",
            b"",
        ])
        mock_session = MagicMock()
        mock_session.get = AsyncMock(return_value=mock_resp)
        client = _make_streaming_client(mock_session)

        task_id = UUID("abcdef01-2345-6789-abcd-ef0123456789")
        async with client.subscribe_background_task_events(task_id) as sse:
            assert isinstance(sse, SSEConnection)
            events = []
            async for event in sse:
                events.append(event)

        assert len(events) == 1
        assert events[0].event == "bgtask_updated"

        call_kwargs = mock_session.get.call_args.kwargs
        assert call_kwargs["params"]["taskId"] == str(task_id)

    @pytest.mark.asyncio
    async def test_stops_on_server_close(self) -> None:
        mock_resp = _make_sse_response([
            b"event: bgtask_done\n",
            b'data: {"task_id": "t1"}\n',
            b"\n",
            b"event: server_close\n",
            b"data: \n",
            b"\n",
            b"event: should_not_appear\n",
            b"data: ignored\n",
            b"\n",
            b"",
        ])
        mock_session = MagicMock()
        mock_session.get = AsyncMock(return_value=mock_resp)
        client = _make_streaming_client(mock_session)

        task_id = UUID("abcdef01-2345-6789-abcd-ef0123456789")
        events = []
        async with client.subscribe_background_task_events(task_id) as sse:
            async for event in sse:
                events.append(event)

        assert len(events) == 2
        assert events[0].event == "bgtask_done"
        assert events[1].event == "server_close"


# ===========================================================================
# REST — Stream apps
# ===========================================================================


class TestGetStreamApps:
    @pytest.mark.asyncio
    async def test_sends_get_and_deserializes(self) -> None:
        mock_resp = AsyncMock()
        mock_resp.status = 200
        mock_resp.json = AsyncMock(
            return_value=[
                {
                    "name": "jupyter",
                    "protocol": "http",
                    "ports": [8080],
                    "url_template": "http://proxy/jupyter",
                },
                {
                    "name": "ttyd",
                    "protocol": "http",
                    "ports": [7681],
                },
            ]
        )
        mock_session = _make_request_session(mock_resp)
        client = _make_streaming_client(mock_session)

        result = await client.get_stream_apps("my-session")

        call_args = mock_session.request.call_args
        assert call_args[0][0] == "GET"
        assert "/stream/session/my-session/apps" in str(call_args[0][1])
        assert isinstance(result, GetStreamAppsResponse)
        assert len(result.root) == 2
        assert result.root[0].name == "jupyter"
        assert result.root[0].protocol == "http"
        assert result.root[0].ports == [8080]
        assert result.root[1].name == "ttyd"

    @pytest.mark.asyncio
    async def test_empty_apps_list(self) -> None:
        mock_resp = AsyncMock()
        mock_resp.status = 200
        mock_resp.json = AsyncMock(return_value=[])
        mock_session = _make_request_session(mock_resp)
        client = _make_streaming_client(mock_session)

        result = await client.get_stream_apps("empty-session")
        assert isinstance(result, GetStreamAppsResponse)
        assert len(result.root) == 0
