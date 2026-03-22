from __future__ import annotations

import uuid

import pytest

from ai.backend.client.exceptions import BackendAPIError
from ai.backend.client.v2.registry import BackendAIClientRegistry
from ai.backend.common.dto.manager.model_serving import (
    RuntimeInfoModel,
    ScaleRequestModel,
    SearchServicesRequestModel,
    SearchServicesResponseModel,
    TokenRequestModel,
    UpdateRouteRequestModel,
)

# ---------------------------------------------------------------------------
# Tier 1: Stateless Read Endpoints (no service setup required)
# ---------------------------------------------------------------------------


class TestListServe:
    async def test_admin_lists_empty_services(
        self,
        admin_registry: BackendAIClientRegistry,
    ) -> None:
        result = await admin_registry.model_serving.list_serve()
        assert isinstance(result, list)
        assert len(result) == 0

    async def test_user_lists_empty_services(
        self,
        user_registry: BackendAIClientRegistry,
    ) -> None:
        result = await user_registry.model_serving.list_serve()
        assert isinstance(result, list)
        assert len(result) == 0

    async def test_list_serve_with_name_filter(
        self,
        admin_registry: BackendAIClientRegistry,
    ) -> None:
        result = await admin_registry.model_serving.list_serve(name="nonexistent")
        assert isinstance(result, list)
        assert len(result) == 0


class TestSearchServices:
    async def test_admin_searches_empty_services(
        self,
        admin_registry: BackendAIClientRegistry,
    ) -> None:
        result = await admin_registry.model_serving.search_services(
            SearchServicesRequestModel(),
        )
        assert isinstance(result, SearchServicesResponseModel)
        assert len(result.items) == 0
        assert result.pagination.total == 0
        assert result.pagination.offset == 0
        assert result.pagination.limit == 20

    async def test_search_with_pagination(
        self,
        admin_registry: BackendAIClientRegistry,
    ) -> None:
        result = await admin_registry.model_serving.search_services(
            SearchServicesRequestModel(offset=0, limit=5),
        )
        assert isinstance(result, SearchServicesResponseModel)
        assert result.pagination.offset == 0
        assert result.pagination.limit == 5


class TestListSupportedRuntimes:
    async def test_admin_lists_runtimes(
        self,
        admin_registry: BackendAIClientRegistry,
    ) -> None:
        result = await admin_registry.model_serving.list_supported_runtimes()
        assert isinstance(result, RuntimeInfoModel)
        assert len(result.runtimes) > 0
        for rt in result.runtimes:
            assert rt.name
            assert rt.human_readable_name

    async def test_user_lists_runtimes(
        self,
        user_registry: BackendAIClientRegistry,
    ) -> None:
        result = await user_registry.model_serving.list_supported_runtimes()
        assert isinstance(result, RuntimeInfoModel)
        assert len(result.runtimes) > 0


# ---------------------------------------------------------------------------
# Tier 2: Error Handling for Non-existent Services
# ---------------------------------------------------------------------------

_RANDOM_SERVICE_ID = uuid.uuid4()
_RANDOM_ROUTE_ID = uuid.uuid4()


class TestGetInfo:
    async def test_get_info_nonexistent_service(
        self,
        admin_registry: BackendAIClientRegistry,
    ) -> None:
        with pytest.raises(BackendAPIError):
            await admin_registry.model_serving.get_info(_RANDOM_SERVICE_ID)


class TestDeleteService:
    async def test_delete_nonexistent_service(
        self,
        admin_registry: BackendAIClientRegistry,
    ) -> None:
        with pytest.raises(BackendAPIError):
            await admin_registry.model_serving.delete(_RANDOM_SERVICE_ID)


class TestSync:
    async def test_sync_nonexistent_service(
        self,
        admin_registry: BackendAIClientRegistry,
    ) -> None:
        with pytest.raises(BackendAPIError):
            await admin_registry.model_serving.sync(_RANDOM_SERVICE_ID)


class TestScale:
    async def test_scale_nonexistent_service(
        self,
        admin_registry: BackendAIClientRegistry,
    ) -> None:
        with pytest.raises(BackendAPIError):
            await admin_registry.model_serving.scale(
                _RANDOM_SERVICE_ID,
                ScaleRequestModel(to=2),
            )


class TestUpdateRoute:
    async def test_update_route_nonexistent_service(
        self,
        admin_registry: BackendAIClientRegistry,
    ) -> None:
        with pytest.raises(BackendAPIError):
            await admin_registry.model_serving.update_route(
                _RANDOM_SERVICE_ID,
                _RANDOM_ROUTE_ID,
                UpdateRouteRequestModel(traffic_ratio=1.0),
            )


class TestDeleteRoute:
    async def test_delete_route_nonexistent_service(
        self,
        admin_registry: BackendAIClientRegistry,
    ) -> None:
        with pytest.raises(BackendAPIError):
            await admin_registry.model_serving.delete_route(
                _RANDOM_SERVICE_ID,
                _RANDOM_ROUTE_ID,
            )


class TestGenerateToken:
    async def test_generate_token_nonexistent_service(
        self,
        admin_registry: BackendAIClientRegistry,
    ) -> None:
        with pytest.raises(BackendAPIError):
            await admin_registry.model_serving.generate_token(
                _RANDOM_SERVICE_ID,
                TokenRequestModel(valid_until=9999999999),
            )


class TestListErrors:
    async def test_list_errors_nonexistent_service(
        self,
        admin_registry: BackendAIClientRegistry,
    ) -> None:
        with pytest.raises(BackendAPIError):
            await admin_registry.model_serving.list_errors(_RANDOM_SERVICE_ID)


class TestClearError:
    async def test_clear_error_nonexistent_service(
        self,
        admin_registry: BackendAIClientRegistry,
    ) -> None:
        with pytest.raises(BackendAPIError):
            await admin_registry.model_serving.clear_error(_RANDOM_SERVICE_ID)
