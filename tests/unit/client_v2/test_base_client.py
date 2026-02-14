from unittest.mock import AsyncMock, MagicMock

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


class TestBackendAIClient:
    @pytest.fixture
    def client(self) -> BackendAIClient:
        config = ClientConfig(endpoint=URL("https://api.example.com"))
        auth = MockAuth()
        return BackendAIClient(config, auth)

    def test_build_url(self, client: BackendAIClient) -> None:
        assert client._build_url("/folders") == "https://api.example.com/folders"
        assert client._build_url("folders") == "https://api.example.com/folders"

    def test_build_url_with_trailing_slash(self) -> None:
        config = ClientConfig(endpoint=URL("https://api.example.com/"))
        client = BackendAIClient(config, MockAuth())
        assert client._build_url("/folders") == "https://api.example.com/folders"

    def test_sign_returns_required_headers(self, client: BackendAIClient) -> None:
        headers = client._sign("GET", "/folders", "application/json")
        assert "Authorization" in headers
        assert "Date" in headers
        assert "Content-Type" in headers
        assert "X-BackendAI-Version" in headers
        assert headers["Content-Type"] == "application/json"

    def test_session_lazy_initialized(self, client: BackendAIClient) -> None:
        assert client._session is None

    def test_docstring_mentions_pydantic(self) -> None:
        assert "Pydantic" in (BackendAIClient.__doc__ or "")

    @pytest.mark.asyncio
    async def test_request_success(self, client: BackendAIClient) -> None:
        mock_resp = AsyncMock()
        mock_resp.status = 200
        mock_resp.json = AsyncMock(return_value={"result": "ok"})

        mock_session = MagicMock()
        mock_ctx = AsyncMock()
        mock_ctx.__aenter__ = AsyncMock(return_value=mock_resp)
        mock_ctx.__aexit__ = AsyncMock(return_value=False)
        mock_session.request = MagicMock(return_value=mock_ctx)

        client._session = mock_session
        result = await client._request("GET", "/test")
        assert result == {"result": "ok"}

    @pytest.mark.asyncio
    async def test_request_raises_on_4xx(self, client: BackendAIClient) -> None:
        mock_resp = AsyncMock()
        mock_resp.status = 404
        mock_resp.reason = "Not Found"
        mock_resp.json = AsyncMock(return_value={"title": "not found"})

        mock_session = MagicMock()
        mock_ctx = AsyncMock()
        mock_ctx.__aenter__ = AsyncMock(return_value=mock_resp)
        mock_ctx.__aexit__ = AsyncMock(return_value=False)
        mock_session.request = MagicMock(return_value=mock_ctx)

        client._session = mock_session
        with pytest.raises(NotFoundError):
            await client._request("GET", "/nonexistent")

    @pytest.mark.asyncio
    async def test_request_raises_on_5xx(self, client: BackendAIClient) -> None:
        mock_resp = AsyncMock()
        mock_resp.status = 500
        mock_resp.reason = "Internal Server Error"
        mock_resp.json = AsyncMock(return_value={"title": "server error"})

        mock_session = MagicMock()
        mock_ctx = AsyncMock()
        mock_ctx.__aenter__ = AsyncMock(return_value=mock_resp)
        mock_ctx.__aexit__ = AsyncMock(return_value=False)
        mock_session.request = MagicMock(return_value=mock_ctx)

        client._session = mock_session
        with pytest.raises(ServerError):
            await client._request("GET", "/error")

    @pytest.mark.asyncio
    async def test_typed_request_deserializes_response(self, client: BackendAIClient) -> None:
        mock_resp = AsyncMock()
        mock_resp.status = 200
        mock_resp.json = AsyncMock(return_value={"name": "test", "count": 42})

        mock_session = MagicMock()
        mock_ctx = AsyncMock()
        mock_ctx.__aenter__ = AsyncMock(return_value=mock_resp)
        mock_ctx.__aexit__ = AsyncMock(return_value=False)
        mock_session.request = MagicMock(return_value=mock_ctx)

        client._session = mock_session
        result = await client.typed_request(
            "GET",
            "/items",
            response_model=SampleResponse,
        )
        assert isinstance(result, SampleResponse)
        assert result.name == "test"
        assert result.count == 42

    @pytest.mark.asyncio
    async def test_typed_request_with_request_model(self, client: BackendAIClient) -> None:
        mock_resp = AsyncMock()
        mock_resp.status = 200
        mock_resp.json = AsyncMock(return_value={"name": "found", "count": 1})

        mock_session = MagicMock()
        mock_ctx = AsyncMock()
        mock_ctx.__aenter__ = AsyncMock(return_value=mock_resp)
        mock_ctx.__aexit__ = AsyncMock(return_value=False)
        mock_session.request = MagicMock(return_value=mock_ctx)

        client._session = mock_session
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
    async def test_close(self, client: BackendAIClient) -> None:
        mock_session = AsyncMock()
        client._session = mock_session
        await client.close()
        mock_session.close.assert_awaited_once()
