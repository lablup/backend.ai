"""Integration tests for model serving via Client SDK v2.

These tests require full infrastructure (agents, AppProxy, storage proxy,
model images) and are structured as lifecycle scenarios. They validate the
complete request/response chain through the real middleware stack.

Note: create() requires a model VFolder + scaling group + image + storage proxy
model definition validation, so services must be pre-provisioned or seeded
by an environment that provides these dependencies.
"""

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


@pytest.mark.integration
class TestModelServingLifecycle:
    """create -> get_info -> list_serve -> search -> scale -> delete

    Requires a running agent, AppProxy, and a model image with a valid
    model VFolder. Skipped in environments without full infrastructure.
    """

    @pytest.mark.asyncio
    async def test_list_and_search_empty(
        self,
        admin_registry: BackendAIClientRegistry,
    ) -> None:
        result = await admin_registry.model_serving.list_serve()
        assert isinstance(result, list)

        search_result = await admin_registry.model_serving.search_services(
            SearchServicesRequestModel(),
        )
        assert isinstance(search_result, SearchServicesResponseModel)
        assert search_result.pagination.total >= 0

    @pytest.mark.asyncio
    async def test_get_info_nonexistent_returns_error(
        self,
        admin_registry: BackendAIClientRegistry,
    ) -> None:
        with pytest.raises(BackendAPIError):
            await admin_registry.model_serving.get_info(uuid.uuid4())

    @pytest.mark.asyncio
    async def test_delete_nonexistent_returns_error(
        self,
        admin_registry: BackendAIClientRegistry,
    ) -> None:
        with pytest.raises(BackendAPIError):
            await admin_registry.model_serving.delete(uuid.uuid4())


@pytest.mark.integration
class TestModelServingTokens:
    """create -> generate_token -> delete

    Token generation requires AppProxy connection. This test verifies
    error handling for nonexistent services.
    """

    @pytest.mark.asyncio
    async def test_generate_token_nonexistent_returns_error(
        self,
        admin_registry: BackendAIClientRegistry,
    ) -> None:
        with pytest.raises(BackendAPIError):
            await admin_registry.model_serving.generate_token(
                uuid.uuid4(),
                TokenRequestModel(valid_until=9999999999),
            )


@pytest.mark.integration
class TestModelServingErrors:
    """create -> list_errors -> clear_error -> delete

    Error listing and clearing require an existing service. This test
    verifies error handling for nonexistent services.
    """

    @pytest.mark.asyncio
    async def test_list_errors_nonexistent_returns_error(
        self,
        admin_registry: BackendAIClientRegistry,
    ) -> None:
        with pytest.raises(BackendAPIError):
            await admin_registry.model_serving.list_errors(uuid.uuid4())

    @pytest.mark.asyncio
    async def test_clear_error_nonexistent_returns_error(
        self,
        admin_registry: BackendAIClientRegistry,
    ) -> None:
        with pytest.raises(BackendAPIError):
            await admin_registry.model_serving.clear_error(uuid.uuid4())


@pytest.mark.integration
class TestModelServingRoutes:
    """create -> update_route -> delete_route -> delete

    Route operations require an existing service with active routes.
    This test verifies error handling for nonexistent services.
    """

    @pytest.mark.asyncio
    async def test_update_route_nonexistent_returns_error(
        self,
        admin_registry: BackendAIClientRegistry,
    ) -> None:
        with pytest.raises(BackendAPIError):
            await admin_registry.model_serving.update_route(
                uuid.uuid4(),
                uuid.uuid4(),
                UpdateRouteRequestModel(traffic_ratio=1.0),
            )

    @pytest.mark.asyncio
    async def test_delete_route_nonexistent_returns_error(
        self,
        admin_registry: BackendAIClientRegistry,
    ) -> None:
        with pytest.raises(BackendAPIError):
            await admin_registry.model_serving.delete_route(
                uuid.uuid4(),
                uuid.uuid4(),
            )


@pytest.mark.integration
class TestModelServingRuntimes:
    @pytest.mark.asyncio
    async def test_list_supported_runtimes(
        self,
        admin_registry: BackendAIClientRegistry,
    ) -> None:
        result = await admin_registry.model_serving.list_supported_runtimes()
        assert isinstance(result, RuntimeInfoModel)
        assert len(result.runtimes) > 0

    @pytest.mark.asyncio
    async def test_scale_nonexistent_returns_error(
        self,
        admin_registry: BackendAIClientRegistry,
    ) -> None:
        with pytest.raises(BackendAPIError):
            await admin_registry.model_serving.scale(
                uuid.uuid4(),
                ScaleRequestModel(to=2),
            )
