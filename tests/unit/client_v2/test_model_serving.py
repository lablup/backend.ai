from __future__ import annotations

import uuid
from unittest.mock import AsyncMock, MagicMock

import pytest
from yarl import URL

from ai.backend.client.v2.base_client import BackendAIClient
from ai.backend.client.v2.config import ClientConfig
from ai.backend.client.v2.domains.model_serving import ModelServingClient
from ai.backend.common.dto.manager.model_serving import (
    ErrorListResponseModel,
    NewServiceRequestModel,
    RuntimeInfoModel,
    ScaleRequestModel,
    ScaleResponseModel,
    SearchServicesRequestModel,
    SearchServicesResponseModel,
    ServeInfoModel,
    SuccessResponseModel,
    TokenRequestModel,
    TokenResponseModel,
    TryStartResponseModel,
    UpdateRouteRequestModel,
)

from .conftest import MockAuth

_SERVICE_ID = uuid.UUID("12345678-1234-1234-1234-123456789abc")
_ROUTE_ID = uuid.UUID("abcdefab-abcd-abcd-abcd-abcdefabcdef")
_DEFAULT_CONFIG = ClientConfig(endpoint=URL("https://api.example.com"))


def _make_mock_client() -> MagicMock:
    """Create a mock BackendAIClient with typed_request and _request stubs."""
    client = MagicMock(spec=BackendAIClient)
    client._config = _DEFAULT_CONFIG
    client._auth = MockAuth()
    client.typed_request = AsyncMock()
    client._request = AsyncMock()
    return client


def _make_model_serving_client(
    mock_client: MagicMock | None = None,
) -> tuple[ModelServingClient, MagicMock]:
    client = mock_client or _make_mock_client()
    return ModelServingClient(client), client


class TestListServe:
    @pytest.mark.asyncio
    async def test_list_serve_calls_request_with_get(self) -> None:
        ms, mock = _make_model_serving_client()
        mock._request.return_value = [
            {
                "id": str(_SERVICE_ID),
                "name": "test-svc",
                "replicas": 1,
                "desired_session_count": 1,
                "active_route_count": 1,
                "service_endpoint": "https://endpoint.example.com",
                "is_public": False,
            }
        ]
        result = await ms.list_serve()
        mock._request.assert_awaited_once_with("GET", "/services", params=None)
        assert len(result) == 1
        assert result[0].name == "test-svc"

    @pytest.mark.asyncio
    async def test_list_serve_with_name_filter(self) -> None:
        ms, mock = _make_model_serving_client()
        mock._request.return_value = []
        await ms.list_serve(name="my-service")
        mock._request.assert_awaited_once_with("GET", "/services", params={"name": "my-service"})

    @pytest.mark.asyncio
    async def test_list_serve_returns_empty_list(self) -> None:
        ms, mock = _make_model_serving_client()
        mock._request.return_value = []
        result = await ms.list_serve()
        assert result == []


class TestSearchServices:
    @pytest.mark.asyncio
    async def test_search_services(self) -> None:
        ms, mock = _make_model_serving_client()
        request = SearchServicesRequestModel(offset=0, limit=10)
        mock.typed_request.return_value = MagicMock(spec=SearchServicesResponseModel)
        result = await ms.search_services(request)
        mock.typed_request.assert_awaited_once_with(
            "POST",
            "/services/_/search",
            request=request,
            response_model=SearchServicesResponseModel,
        )
        assert result is mock.typed_request.return_value


class TestGetInfo:
    @pytest.mark.asyncio
    async def test_get_info(self) -> None:
        ms, mock = _make_model_serving_client()
        mock.typed_request.return_value = MagicMock(spec=ServeInfoModel)
        result = await ms.get_info(_SERVICE_ID)
        mock.typed_request.assert_awaited_once_with(
            "GET",
            f"/services/{_SERVICE_ID}",
            response_model=ServeInfoModel,
        )
        assert result is mock.typed_request.return_value


class TestCreate:
    @pytest.mark.asyncio
    async def test_create(self) -> None:
        ms, mock = _make_model_serving_client()
        request = MagicMock(spec=NewServiceRequestModel)
        mock.typed_request.return_value = MagicMock(spec=ServeInfoModel)
        result = await ms.create(request)
        mock.typed_request.assert_awaited_once_with(
            "POST",
            "/services",
            request=request,
            response_model=ServeInfoModel,
        )
        assert result is mock.typed_request.return_value


class TestTryStart:
    @pytest.mark.asyncio
    async def test_try_start(self) -> None:
        ms, mock = _make_model_serving_client()
        request = MagicMock(spec=NewServiceRequestModel)
        mock.typed_request.return_value = MagicMock(spec=TryStartResponseModel)
        result = await ms.try_start(request)
        mock.typed_request.assert_awaited_once_with(
            "POST",
            "/services/_/try",
            request=request,
            response_model=TryStartResponseModel,
        )
        assert result is mock.typed_request.return_value


class TestDelete:
    @pytest.mark.asyncio
    async def test_delete(self) -> None:
        ms, mock = _make_model_serving_client()
        mock.typed_request.return_value = MagicMock(spec=SuccessResponseModel)
        result = await ms.delete(_SERVICE_ID)
        mock.typed_request.assert_awaited_once_with(
            "DELETE",
            f"/services/{_SERVICE_ID}",
            response_model=SuccessResponseModel,
        )
        assert result is mock.typed_request.return_value


class TestSync:
    @pytest.mark.asyncio
    async def test_sync(self) -> None:
        ms, mock = _make_model_serving_client()
        mock.typed_request.return_value = MagicMock(spec=SuccessResponseModel)
        result = await ms.sync(_SERVICE_ID)
        mock.typed_request.assert_awaited_once_with(
            "POST",
            f"/services/{_SERVICE_ID}/sync",
            response_model=SuccessResponseModel,
        )
        assert result is mock.typed_request.return_value


class TestScale:
    @pytest.mark.asyncio
    async def test_scale(self) -> None:
        ms, mock = _make_model_serving_client()
        request = ScaleRequestModel(to=3)
        mock.typed_request.return_value = MagicMock(spec=ScaleResponseModel)
        result = await ms.scale(_SERVICE_ID, request)
        mock.typed_request.assert_awaited_once_with(
            "POST",
            f"/services/{_SERVICE_ID}/scale",
            request=request,
            response_model=ScaleResponseModel,
        )
        assert result is mock.typed_request.return_value


class TestUpdateRoute:
    @pytest.mark.asyncio
    async def test_update_route(self) -> None:
        ms, mock = _make_model_serving_client()
        request = UpdateRouteRequestModel(traffic_ratio=0.5)
        mock.typed_request.return_value = MagicMock(spec=SuccessResponseModel)
        result = await ms.update_route(_SERVICE_ID, _ROUTE_ID, request)
        mock.typed_request.assert_awaited_once_with(
            "PUT",
            f"/services/{_SERVICE_ID}/routings/{_ROUTE_ID}",
            request=request,
            response_model=SuccessResponseModel,
        )
        assert result is mock.typed_request.return_value


class TestDeleteRoute:
    @pytest.mark.asyncio
    async def test_delete_route(self) -> None:
        ms, mock = _make_model_serving_client()
        mock.typed_request.return_value = MagicMock(spec=SuccessResponseModel)
        result = await ms.delete_route(_SERVICE_ID, _ROUTE_ID)
        mock.typed_request.assert_awaited_once_with(
            "DELETE",
            f"/services/{_SERVICE_ID}/routings/{_ROUTE_ID}",
            response_model=SuccessResponseModel,
        )
        assert result is mock.typed_request.return_value


class TestGenerateToken:
    @pytest.mark.asyncio
    async def test_generate_token(self) -> None:
        ms, mock = _make_model_serving_client()
        request = MagicMock(spec=TokenRequestModel)
        mock.typed_request.return_value = MagicMock(spec=TokenResponseModel)
        result = await ms.generate_token(_SERVICE_ID, request)
        mock.typed_request.assert_awaited_once_with(
            "POST",
            f"/services/{_SERVICE_ID}/token",
            request=request,
            response_model=TokenResponseModel,
        )
        assert result is mock.typed_request.return_value


class TestListErrors:
    @pytest.mark.asyncio
    async def test_list_errors(self) -> None:
        ms, mock = _make_model_serving_client()
        mock.typed_request.return_value = MagicMock(spec=ErrorListResponseModel)
        result = await ms.list_errors(_SERVICE_ID)
        mock.typed_request.assert_awaited_once_with(
            "GET",
            f"/services/{_SERVICE_ID}/errors",
            response_model=ErrorListResponseModel,
        )
        assert result is mock.typed_request.return_value


class TestClearError:
    @pytest.mark.asyncio
    async def test_clear_error_calls_typed_request_no_content(self) -> None:
        ms, mock = _make_model_serving_client()
        mock.typed_request_no_content = AsyncMock()
        await ms.clear_error(_SERVICE_ID)
        mock.typed_request_no_content.assert_awaited_once_with(
            "POST",
            f"/services/{_SERVICE_ID}/errors/clear",
        )


class TestListSupportedRuntimes:
    @pytest.mark.asyncio
    async def test_list_supported_runtimes(self) -> None:
        ms, mock = _make_model_serving_client()
        mock.typed_request.return_value = MagicMock(spec=RuntimeInfoModel)
        result = await ms.list_supported_runtimes()
        mock.typed_request.assert_awaited_once_with(
            "GET",
            "/services/_/runtimes",
            response_model=RuntimeInfoModel,
        )
        assert result is mock.typed_request.return_value
