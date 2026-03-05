"""
Component tests for Model Serving SDK client route methods.

These tests verify HTTP routing, request/response serialization,
and error handling for Model Serving (legacy service) API endpoints
via the Client SDK.
"""

from __future__ import annotations

import uuid

import pytest

from ai.backend.client.exceptions import BackendAPIError
from ai.backend.client.v2.registry import BackendAIClientRegistry
from ai.backend.common.dto.manager.model_serving import (
    NewServiceRequestModel,
    ScaleRequestModel,
    ServiceConfigModel,
    TokenRequestModel,
)

_RANDOM_SERVICE_ID = uuid.uuid4()
_RANDOM_ROUTE_ID = uuid.uuid4()


# ---------------------------------------------------------------------------
# SDK service.create() — deployment creation via legacy service API
# ---------------------------------------------------------------------------


class TestCreateService:
    async def test_create_service_missing_image_returns_error(
        self,
        admin_registry: BackendAIClientRegistry,
    ) -> None:
        """Creating a service with a non-existent image raises BackendAPIError."""
        request = NewServiceRequestModel(
            service_name="test-service-create",
            replicas=1,
            image="cr.backend.ai/nonexistent/image:latest",
            group_name="default",
            domain_name="default",
            config=ServiceConfigModel(
                model="nonexistent-model-vfolder",
                model_definition_path="model-definition.yaml",
                scaling_group="nonexistent-sgroup",
            ),
        )
        with pytest.raises(BackendAPIError):
            await admin_registry.model_serving.create(request)

    async def test_user_create_service_returns_error(
        self,
        user_registry: BackendAIClientRegistry,
    ) -> None:
        """Regular user creating a service with non-existent resources raises error."""
        request = NewServiceRequestModel(
            service_name="test-user-service",
            replicas=1,
            image="cr.backend.ai/nonexistent/image:latest",
            group_name="default",
            domain_name="default",
            config=ServiceConfigModel(
                model="nonexistent-model",
                model_definition_path="model-definition.yaml",
                scaling_group="nonexistent-sgroup",
            ),
        )
        with pytest.raises(BackendAPIError):
            await user_registry.model_serving.create(request)


# ---------------------------------------------------------------------------
# SDK service.scale() — replica count change
# ---------------------------------------------------------------------------


class TestScaleService:
    async def test_scale_nonexistent_service_raises_error(
        self,
        admin_registry: BackendAIClientRegistry,
    ) -> None:
        """Scaling a non-existent service raises BackendAPIError."""
        with pytest.raises(BackendAPIError):
            await admin_registry.model_serving.scale(
                _RANDOM_SERVICE_ID,
                ScaleRequestModel(to=5),
            )

    async def test_user_scale_nonexistent_service(
        self,
        user_registry: BackendAIClientRegistry,
    ) -> None:
        """Regular user scaling a non-existent service raises BackendAPIError."""
        with pytest.raises(BackendAPIError):
            await user_registry.model_serving.scale(
                _RANDOM_SERVICE_ID,
                ScaleRequestModel(to=3),
            )


# ---------------------------------------------------------------------------
# SDK service.sync() — route synchronization
# ---------------------------------------------------------------------------


class TestSyncService:
    async def test_sync_nonexistent_service_raises_error(
        self,
        admin_registry: BackendAIClientRegistry,
    ) -> None:
        """Syncing a non-existent service raises BackendAPIError."""
        with pytest.raises(BackendAPIError):
            await admin_registry.model_serving.sync(_RANDOM_SERVICE_ID)

    async def test_user_sync_nonexistent_service(
        self,
        user_registry: BackendAIClientRegistry,
    ) -> None:
        """Regular user syncing a non-existent service raises BackendAPIError."""
        with pytest.raises(BackendAPIError):
            await user_registry.model_serving.sync(_RANDOM_SERVICE_ID)


# ---------------------------------------------------------------------------
# SDK service.generate_api_token() — access token creation
# ---------------------------------------------------------------------------


class TestGenerateApiToken:
    async def test_generate_token_nonexistent_service_raises_error(
        self,
        admin_registry: BackendAIClientRegistry,
    ) -> None:
        """Generating a token for a non-existent service raises BackendAPIError."""
        with pytest.raises(BackendAPIError):
            await admin_registry.model_serving.generate_token(
                _RANDOM_SERVICE_ID,
                TokenRequestModel(valid_until=9999999999),
            )

    async def test_user_generate_token_nonexistent_service(
        self,
        user_registry: BackendAIClientRegistry,
    ) -> None:
        """Regular user generating a token for non-existent service raises error."""
        with pytest.raises(BackendAPIError):
            await user_registry.model_serving.generate_token(
                _RANDOM_SERVICE_ID,
                TokenRequestModel(valid_until=9999999999),
            )


# ---------------------------------------------------------------------------
# SDK service.delete() — deployment deletion
# ---------------------------------------------------------------------------


class TestDeleteService:
    async def test_delete_nonexistent_service_raises_error(
        self,
        admin_registry: BackendAIClientRegistry,
    ) -> None:
        """Deleting a non-existent service raises BackendAPIError."""
        with pytest.raises(BackendAPIError):
            await admin_registry.model_serving.delete(_RANDOM_SERVICE_ID)

    async def test_user_delete_nonexistent_service(
        self,
        user_registry: BackendAIClientRegistry,
    ) -> None:
        """Regular user deleting a non-existent service raises BackendAPIError."""
        with pytest.raises(BackendAPIError):
            await user_registry.model_serving.delete(_RANDOM_SERVICE_ID)


# ---------------------------------------------------------------------------
# SDK service.delete_route() — route deletion
# ---------------------------------------------------------------------------


class TestDeleteRouteService:
    async def test_delete_route_nonexistent_service_raises_error(
        self,
        admin_registry: BackendAIClientRegistry,
    ) -> None:
        """Deleting a route from non-existent service raises BackendAPIError."""
        with pytest.raises(BackendAPIError):
            await admin_registry.model_serving.delete_route(
                _RANDOM_SERVICE_ID,
                _RANDOM_ROUTE_ID,
            )
