from collections.abc import AsyncIterator
from unittest.mock import AsyncMock, MagicMock, PropertyMock, patch

import aiohttp
import pytest
from yarl import URL

from ai.backend.client.exceptions import BackendAPIError
from ai.backend.client.v2.base_client import BackendAIClient
from ai.backend.client.v2.config import ClientConfig
from ai.backend.client.v2.exceptions import (
    AuthenticationError,
    NotFoundError,
    ServerError,
    SSEError,
    WebSocketError,
)
from ai.backend.client.v2.streaming_types import SSEConnection, SSEEvent, WebSocketSession
from ai.backend.common.api_handlers import BaseRequestModel, BaseResponseModel

from .conftest import MockAuth


class SampleResponse(BaseResponseModel):
    name: str
    count: int


class SampleRequest(BaseRequestModel):
    query: str


_DEFAULT_CONFIG = ClientConfig(endpoint=URL("https://api.example.com"))


def _make_client(
    mock_session: MagicMock | None = None,
    config: ClientConfig | None = None,
) -> BackendAIClient:
    return BackendAIClient(
        config or _DEFAULT_CONFIG,
        MockAuth(),
        mock_session or MagicMock(),
    )


def _make_request_session(resp: AsyncMock) -> MagicMock:
    """Build a mock session whose ``request()`` returns *resp* as a context manager."""
    mock_ctx = AsyncMock()
    mock_ctx.__aenter__ = AsyncMock(return_value=resp)
    mock_ctx.__aexit__ = AsyncMock(return_value=False)

    mock_session = MagicMock()
    mock_session.request = MagicMock(return_value=mock_ctx)
    return mock_session


class TestBackendAIClient:
    def test_build_url(self) -> None:
        client = _make_client()
        assert client._build_url("/folders") == "https://api.example.com/folders"
        assert client._build_url("folders") == "https://api.example.com/folders"

    def test_build_url_with_trailing_slash(self) -> None:
        config = ClientConfig(endpoint=URL("https://api.example.com/"))
        client = _make_client(config=config)
        assert client._build_url("/folders") == "https://api.example.com/folders"

    def test_sign_returns_required_headers(self) -> None:
        client = _make_client()
        headers = client._sign("GET", "/folders", "application/json")
        assert "Authorization" in headers
        assert "Date" in headers
        assert "Content-Type" in headers
        assert "X-BackendAI-Version" in headers
        assert headers["Content-Type"] == "application/json"

    def test_docstring_mentions_pydantic(self) -> None:
        assert "Pydantic" in (BackendAIClient.__doc__ or "")

    @pytest.mark.asyncio
    async def test_create_factory(self) -> None:
        config = ClientConfig(endpoint=URL("https://api.example.com"))
        with patch("ai.backend.client.v2.base_client.aiohttp.ClientSession") as mock_cls:
            mock_session = MagicMock()
            mock_cls.return_value = mock_session
            client = await BackendAIClient.create(config, MockAuth())
            assert client._session is mock_session
            mock_cls.assert_called_once()

    @pytest.mark.asyncio
    async def test_request_success(self) -> None:
        mock_resp = AsyncMock()
        mock_resp.status = 200
        mock_resp.json = AsyncMock(return_value={"result": "ok"})

        mock_session = _make_request_session(mock_resp)
        client = _make_client(mock_session)
        result = await client._request("GET", "/test")
        assert result == {"result": "ok"}

    @pytest.mark.asyncio
    async def test_request_raises_on_4xx(self) -> None:
        mock_resp = AsyncMock()
        mock_resp.status = 404
        mock_resp.reason = "Not Found"
        mock_resp.json = AsyncMock(return_value={"title": "not found"})

        mock_session = _make_request_session(mock_resp)
        client = _make_client(mock_session)
        with pytest.raises(NotFoundError):
            await client._request("GET", "/nonexistent")

    @pytest.mark.asyncio
    async def test_request_raises_on_5xx(self) -> None:
        mock_resp = AsyncMock()
        mock_resp.status = 500
        mock_resp.reason = "Internal Server Error"
        mock_resp.json = AsyncMock(return_value={"title": "server error"})

        mock_session = _make_request_session(mock_resp)
        client = _make_client(mock_session)
        with pytest.raises(ServerError):
            await client._request("GET", "/error")

    @pytest.mark.asyncio
    async def test_typed_request_deserializes_response(self) -> None:
        mock_resp = AsyncMock()
        mock_resp.status = 200
        mock_resp.json = AsyncMock(return_value={"name": "test", "count": 42})

        mock_session = _make_request_session(mock_resp)
        client = _make_client(mock_session)
        result = await client.typed_request(
            "GET",
            "/items",
            response_model=SampleResponse,
        )
        assert isinstance(result, SampleResponse)
        assert result.name == "test"
        assert result.count == 42

    @pytest.mark.asyncio
    async def test_typed_request_with_request_model(self) -> None:
        mock_resp = AsyncMock()
        mock_resp.status = 200
        mock_resp.json = AsyncMock(return_value={"name": "found", "count": 1})

        mock_session = _make_request_session(mock_resp)
        client = _make_client(mock_session)
        result = await client.typed_request(
            "POST",
            "/search",
            request=SampleRequest(query="test"),
            response_model=SampleResponse,
        )
        assert isinstance(result, SampleResponse)
        call_kwargs = mock_session.request.call_args
        assert call_kwargs.kwargs["json"] == {"query": "test"}

    @pytest.mark.asyncio
    async def test_close(self) -> None:
        mock_session = AsyncMock()
        client = _make_client(mock_session)
        await client.close()
        mock_session.close.assert_awaited_once()

    @pytest.mark.asyncio
    async def test_request_returns_none_on_204(self) -> None:
        mock_resp = AsyncMock()
        mock_resp.status = 204

        mock_session = _make_request_session(mock_resp)
        client = _make_client(mock_session)
        result = await client._request("DELETE", "/resource/123")
        assert result is None

    @pytest.mark.asyncio
    async def test_typed_request_no_content_success(self) -> None:
        mock_resp = AsyncMock()
        mock_resp.status = 204

        mock_session = _make_request_session(mock_resp)
        client = _make_client(mock_session)
        await client.typed_request_no_content("DELETE", "/resource/123")

    @pytest.mark.asyncio
    async def test_typed_request_no_content_with_request_body(self) -> None:
        mock_resp = AsyncMock()
        mock_resp.status = 204

        mock_session = _make_request_session(mock_resp)
        client = _make_client(mock_session)
        await client.typed_request_no_content(
            "PUT",
            "/resource/123",
            request=SampleRequest(query="update"),
        )
        call_kwargs = mock_session.request.call_args
        assert call_kwargs.kwargs["json"] == {"query": "update"}

    @pytest.mark.asyncio
    async def test_typed_request_raises_on_unexpected_204(self) -> None:
        mock_resp = AsyncMock()
        mock_resp.status = 204

        mock_session = _make_request_session(mock_resp)
        client = _make_client(mock_session)
        with pytest.raises(BackendAPIError) as exc_info:
            await client.typed_request(
                "GET",
                "/items",
                response_model=SampleResponse,
            )
        assert exc_info.value.status == 204


class TestUpload:
    @pytest.mark.asyncio
    async def test_upload_success_json_response(self) -> None:
        mock_resp = AsyncMock()
        mock_resp.status = 200
        mock_resp.json = AsyncMock(return_value={"uploaded": True})

        mock_session = _make_request_session(mock_resp)
        client = _make_client(mock_session)
        form_data = aiohttp.FormData()
        form_data.add_field("src", b"file-content", filename="test.txt")

        result = await client.upload("/session/my-sess/upload", form_data)

        assert result == {"uploaded": True}
        call_args = mock_session.request.call_args
        assert call_args.args[0] == "POST"
        headers = call_args.kwargs["headers"]
        assert "Authorization" in headers
        assert "Content-Type" not in headers

    @pytest.mark.asyncio
    async def test_upload_returns_none_on_204(self) -> None:
        mock_resp = AsyncMock()
        mock_resp.status = 204

        mock_session = _make_request_session(mock_resp)
        client = _make_client(mock_session)
        form_data = aiohttp.FormData()

        result = await client.upload("/session/my-sess/upload", form_data)

        assert result is None

    @pytest.mark.asyncio
    async def test_upload_raises_on_error(self) -> None:
        mock_resp = AsyncMock()
        mock_resp.status = 500
        mock_resp.reason = "Internal Server Error"
        mock_resp.json = AsyncMock(return_value={"title": "server error"})

        mock_session = _make_request_session(mock_resp)
        client = _make_client(mock_session)
        form_data = aiohttp.FormData()

        with pytest.raises(ServerError):
            await client.upload("/session/my-sess/upload", form_data)


class TestDownload:
    @pytest.mark.asyncio
    async def test_download_returns_bytes(self) -> None:
        mock_resp = AsyncMock()
        mock_resp.status = 200
        mock_resp.read = AsyncMock(return_value=b"binary-content")

        mock_session = _make_request_session(mock_resp)
        client = _make_client(mock_session)

        result = await client.download("/session/my-sess/download", json={"files": ["a.txt"]})

        assert result == b"binary-content"
        call_args = mock_session.request.call_args
        assert call_args.args[0] == "POST"
        assert call_args.kwargs["json"] == {"files": ["a.txt"]}

    @pytest.mark.asyncio
    async def test_download_with_get_method(self) -> None:
        mock_resp = AsyncMock()
        mock_resp.status = 200
        mock_resp.read = AsyncMock(return_value=b"log-data")

        mock_session = _make_request_session(mock_resp)
        client = _make_client(mock_session)

        result = await client.download("/session/_/logs", method="GET", params={"taskId": "t-1"})

        assert result == b"log-data"
        call_args = mock_session.request.call_args
        assert call_args.args[0] == "GET"
        assert call_args.kwargs["params"] == {"taskId": "t-1"}

    @pytest.mark.asyncio
    async def test_download_raises_on_error(self) -> None:
        mock_resp = AsyncMock()
        mock_resp.status = 404
        mock_resp.reason = "Not Found"
        mock_resp.json = AsyncMock(return_value={"title": "not found"})

        mock_session = _make_request_session(mock_resp)
        client = _make_client(mock_session)

        with pytest.raises(NotFoundError):
            await client.download("/session/my-sess/download")


def _make_mock_ws(*, closed: bool = False) -> MagicMock:
    """Build a mock ``aiohttp.ClientWebSocketResponse``."""
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


def _make_sse_response_body(lines: list[bytes]) -> AsyncMock:
    """Build a mock ``aiohttp.ClientResponse`` whose content yields *lines*."""
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


class TestWSConnect:
    @pytest.mark.asyncio
    async def test_ws_connect_success(self) -> None:
        mock_ws = _make_mock_ws()
        mock_session = MagicMock()
        mock_session.ws_connect = AsyncMock(return_value=mock_ws)
        client = _make_client(mock_session)

        async with client.ws_connect("/stream/test") as ws:
            assert isinstance(ws, WebSocketSession)
            assert not ws.closed

        # Verify auth headers were passed.
        call_kwargs = mock_session.ws_connect.call_args
        headers = call_kwargs.kwargs["headers"]
        assert "Authorization" in headers
        assert "X-BackendAI-Version" in headers

    @pytest.mark.asyncio
    async def test_ws_connect_send_receive(self) -> None:
        mock_ws = _make_mock_ws()
        mock_session = MagicMock()
        mock_session.ws_connect = AsyncMock(return_value=mock_ws)
        client = _make_client(mock_session)

        async with client.ws_connect("/stream/test") as ws:
            await ws.send_str("ping")
            result = await ws.receive_str()
            assert result == "hello"

            await ws.send_bytes(b"data")
            result_bytes = await ws.receive_bytes()
            assert result_bytes == b"bytes"

            await ws.send_json({"a": 1})
            result_json = await ws.receive_json()
            assert result_json == {"key": "value"}

        mock_ws.send_str.assert_awaited_once_with("ping")
        mock_ws.send_bytes.assert_awaited_once_with(b"data")
        mock_ws.send_json.assert_awaited_once_with({"a": 1})

    @pytest.mark.asyncio
    async def test_ws_connect_async_iteration(self) -> None:
        mock_ws = _make_mock_ws()
        msg1 = MagicMock(spec=aiohttp.WSMessage)
        msg1.data = "first"
        msg2 = MagicMock(spec=aiohttp.WSMessage)
        msg2.data = "second"

        async def _aiter() -> AsyncIterator[aiohttp.WSMessage]:
            for m in [msg1, msg2]:
                yield m

        mock_ws.__aiter__ = lambda self: _aiter()

        mock_session = MagicMock()
        mock_session.ws_connect = AsyncMock(return_value=mock_ws)
        client = _make_client(mock_session)

        collected = []
        async with client.ws_connect("/stream/test") as ws:
            async for msg in ws:
                collected.append(msg.data)
        assert collected == ["first", "second"]

    @pytest.mark.asyncio
    async def test_ws_connect_connection_error(self) -> None:
        mock_session = MagicMock()
        mock_session.ws_connect = AsyncMock(
            side_effect=aiohttp.ClientConnectionError("connection refused")
        )
        client = _make_client(mock_session)

        with pytest.raises(WebSocketError):
            async with client.ws_connect("/stream/test"):
                pass

    @pytest.mark.asyncio
    async def test_ws_connect_closed_send_raises(self) -> None:
        mock_ws = _make_mock_ws(closed=True)
        mock_session = MagicMock()
        mock_session.ws_connect = AsyncMock(return_value=mock_ws)
        client = _make_client(mock_session)

        # The ws_connect itself succeeds (we get back the closed mock),
        # but operations on it raise.
        async with client.ws_connect("/stream/test") as ws:
            with pytest.raises(WebSocketError):
                await ws.send_str("should fail")

    @pytest.mark.asyncio
    async def test_ws_connect_handshake_error(self) -> None:
        mock_session = MagicMock()
        mock_session.ws_connect = AsyncMock(
            side_effect=aiohttp.WSServerHandshakeError(
                request_info=MagicMock(),
                history=(),
                status=401,
                message="Unauthorized",
                headers=MagicMock(),
            )
        )
        client = _make_client(mock_session)

        with pytest.raises(AuthenticationError):
            async with client.ws_connect("/stream/test"):
                pass


class TestSSEConnect:
    @pytest.mark.asyncio
    async def test_sse_connect_success(self) -> None:
        mock_resp = _make_sse_response_body([
            b"event: ping\n",
            b"data: hello\n",
            b"\n",
        ])
        mock_session = MagicMock()
        mock_session.get = AsyncMock(return_value=mock_resp)
        client = _make_client(mock_session)

        async with client.sse_connect("/events/test") as conn:
            assert isinstance(conn, SSEConnection)

        # Verify auth headers.
        call_kwargs = mock_session.get.call_args
        headers = call_kwargs.kwargs["headers"]
        assert "Authorization" in headers
        assert headers["Accept"] == "text/event-stream"

    @pytest.mark.asyncio
    async def test_sse_connect_parses_events(self) -> None:
        mock_resp = _make_sse_response_body([
            b"event: update\n",
            b"data: payload1\n",
            b"id: 1\n",
            b"\n",
            b"event: update\n",
            b"data: payload2\n",
            b"id: 2\n",
            b"retry: 5000\n",
            b"\n",
        ])
        mock_session = MagicMock()
        mock_session.get = AsyncMock(return_value=mock_resp)
        client = _make_client(mock_session)

        events: list[SSEEvent] = []
        async with client.sse_connect("/events/test") as conn:
            async for event in conn:
                events.append(event)

        assert len(events) == 2
        assert events[0] == SSEEvent(event="update", data="payload1", id="1", retry=None)
        assert events[1] == SSEEvent(event="update", data="payload2", id="2", retry=5000)

    @pytest.mark.asyncio
    async def test_sse_connect_multi_line_data(self) -> None:
        mock_resp = _make_sse_response_body([
            b"data: line1\n",
            b"data: line2\n",
            b"data: line3\n",
            b"\n",
        ])
        mock_session = MagicMock()
        mock_session.get = AsyncMock(return_value=mock_resp)
        client = _make_client(mock_session)

        events: list[SSEEvent] = []
        async with client.sse_connect("/events/test") as conn:
            async for event in conn:
                events.append(event)

        assert len(events) == 1
        assert events[0].data == "line1\nline2\nline3"

    @pytest.mark.asyncio
    async def test_sse_connect_ignores_comments(self) -> None:
        mock_resp = _make_sse_response_body([
            b": this is a comment\n",
            b"data: actual\n",
            b"\n",
        ])
        mock_session = MagicMock()
        mock_session.get = AsyncMock(return_value=mock_resp)
        client = _make_client(mock_session)

        events: list[SSEEvent] = []
        async with client.sse_connect("/events/test") as conn:
            async for event in conn:
                events.append(event)

        assert len(events) == 1
        assert events[0].data == "actual"

    @pytest.mark.asyncio
    async def test_sse_connect_server_close(self) -> None:
        mock_resp = _make_sse_response_body([
            b"data: first\n",
            b"\n",
            b"event: server_close\n",
            b"data: bye\n",
            b"\n",
            b"data: should_not_appear\n",
            b"\n",
        ])
        mock_session = MagicMock()
        mock_session.get = AsyncMock(return_value=mock_resp)
        client = _make_client(mock_session)

        events: list[SSEEvent] = []
        async with client.sse_connect("/events/test") as conn:
            async for event in conn:
                events.append(event)

        assert len(events) == 2
        assert events[0].event == "message"
        assert events[0].data == "first"
        assert events[1].event == "server_close"
        assert events[1].data == "bye"

    @pytest.mark.asyncio
    async def test_sse_connect_http_error(self) -> None:
        mock_resp = AsyncMock(spec=aiohttp.ClientResponse)
        mock_resp.status = 401
        mock_resp.reason = "Unauthorized"
        mock_resp.json = AsyncMock(return_value={"title": "Unauthorized"})
        mock_resp.close = MagicMock()

        mock_session = MagicMock()
        mock_session.get = AsyncMock(return_value=mock_resp)
        client = _make_client(mock_session)

        with pytest.raises(AuthenticationError):
            async with client.sse_connect("/events/test"):
                pass

    @pytest.mark.asyncio
    async def test_sse_connect_connection_error(self) -> None:
        mock_session = MagicMock()
        mock_session.get = AsyncMock(
            side_effect=aiohttp.ClientConnectionError("connection refused")
        )
        client = _make_client(mock_session)

        with pytest.raises(SSEError):
            async with client.sse_connect("/events/test"):
                pass

    @pytest.mark.asyncio
    async def test_sse_connect_default_event_type(self) -> None:
        """Events without explicit ``event:`` field default to ``message``."""
        mock_resp = _make_sse_response_body([
            b"data: hello\n",
            b"\n",
        ])
        mock_session = MagicMock()
        mock_session.get = AsyncMock(return_value=mock_resp)
        client = _make_client(mock_session)

        events: list[SSEEvent] = []
        async with client.sse_connect("/events/test") as conn:
            async for event in conn:
                events.append(event)

        assert len(events) == 1
        assert events[0].event == "message"
        assert events[0].data == "hello"
