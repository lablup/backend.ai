from unittest.mock import AsyncMock, MagicMock

import pytest
from yarl import URL

from ai.backend.client.v2.base_client import BackendAIClient
from ai.backend.client.v2.config import ClientConfig
from ai.backend.client.v2.domains.streaming import (
    GetStreamAppsResponseItem,
    ShutdownServiceRequest,
    StartServiceRequest,
    StartServiceResponse,
    StreamingClient,
)

from .conftest import MockAuth

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


class TestStreamingClient:
    @pytest.mark.asyncio
    async def test_get_stream_apps_returns_typed_response(self) -> None:
        mock_resp = AsyncMock()
        mock_resp.status = 200
        mock_resp.json = AsyncMock(
            return_value=[
                {
                    "name": "ttyd",
                    "protocol": "http",
                    "ports": [7681],
                    "url_template": "/v2/proxy/{port}",
                },
                {
                    "name": "jupyter",
                    "protocol": "http",
                    "ports": [8080, 8443],
                    "allowed_envs": {"PASSWORD": "string"},
                },
            ]
        )

        mock_session = _make_request_session(mock_resp)
        base_client = _make_client(mock_session)
        streaming = StreamingClient(base_client)

        result = await streaming.get_stream_apps("my-session")

        assert len(result) == 2
        assert all(isinstance(item, GetStreamAppsResponseItem) for item in result)
        assert result[0].name == "ttyd"
        assert result[0].protocol == "http"
        assert result[0].ports == [7681]
        assert result[0].url_template == "/v2/proxy/{port}"
        assert result[0].allowed_envs is None
        assert result[1].name == "jupyter"
        assert result[1].ports == [8080, 8443]
        assert result[1].allowed_envs == {"PASSWORD": "string"}

        call_args = mock_session.request.call_args
        assert call_args.args[0] == "GET"
        assert "/stream/session/my-session/apps" in str(call_args.args[1])

    @pytest.mark.asyncio
    async def test_get_stream_apps_empty_list(self) -> None:
        mock_resp = AsyncMock()
        mock_resp.status = 200
        mock_resp.json = AsyncMock(return_value=[])

        mock_session = _make_request_session(mock_resp)
        base_client = _make_client(mock_session)
        streaming = StreamingClient(base_client)

        result = await streaming.get_stream_apps("my-session")

        assert result == []

    @pytest.mark.asyncio
    async def test_start_service_sends_request(self) -> None:
        mock_resp = AsyncMock()
        mock_resp.status = 200
        mock_resp.json = AsyncMock(
            return_value={
                "token": "abc123",
                "wsproxy_addr": "ws://proxy.example.com:10200",
            }
        )

        mock_session = _make_request_session(mock_resp)
        base_client = _make_client(mock_session)
        streaming = StreamingClient(base_client)

        req = StartServiceRequest(
            app="jupyter",
            port=8080,
            envs='{"PASSWORD": "secret"}',
        )
        result = await streaming.start_service("my-session", req)

        assert isinstance(result, StartServiceResponse)
        assert result.token == "abc123"
        assert result.wsproxy_addr == "ws://proxy.example.com:10200"

        call_args = mock_session.request.call_args
        assert call_args.args[0] == "POST"
        assert "/sessions/my-session/start-service" in str(call_args.args[1])
        body = call_args.kwargs["json"]
        assert body["app"] == "jupyter"
        assert body["port"] == 8080
        assert body["envs"] == '{"PASSWORD": "secret"}'
        assert "arguments" not in body
        assert "login_session_token" not in body

    @pytest.mark.asyncio
    async def test_start_service_minimal_request(self) -> None:
        mock_resp = AsyncMock()
        mock_resp.status = 200
        mock_resp.json = AsyncMock(
            return_value={
                "token": "tok",
                "wsproxy_addr": "ws://proxy:10200",
            }
        )

        mock_session = _make_request_session(mock_resp)
        base_client = _make_client(mock_session)
        streaming = StreamingClient(base_client)

        req = StartServiceRequest(app="ttyd")
        result = await streaming.start_service("sess", req)

        assert result.token == "tok"

        call_args = mock_session.request.call_args
        body = call_args.kwargs["json"]
        assert body == {"app": "ttyd"}

    @pytest.mark.asyncio
    async def test_shutdown_service_sends_request(self) -> None:
        mock_resp = AsyncMock()
        mock_resp.status = 204
        mock_resp.json = AsyncMock(side_effect=Exception("no body"))

        mock_session = _make_request_session(mock_resp)
        base_client = _make_client(mock_session)
        streaming = StreamingClient(base_client)

        req = ShutdownServiceRequest(service_name="jupyter")
        await streaming.shutdown_service("my-session", req)

        call_args = mock_session.request.call_args
        assert call_args.args[0] == "POST"
        assert "/sessions/my-session/shutdown-service" in str(call_args.args[1])
        body = call_args.kwargs["json"]
        assert body == {"service_name": "jupyter"}
