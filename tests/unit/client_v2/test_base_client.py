from unittest.mock import AsyncMock, MagicMock, patch

import pytest
from yarl import URL

from ai.backend.client.v2.base_client import BackendAIClient
from ai.backend.client.v2.config import ClientConfig
from ai.backend.client.v2.exceptions import NotFoundError, ServerError
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
