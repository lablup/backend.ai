from __future__ import annotations

import uuid

import pytest

from ai.backend.client.v2.exceptions import PermissionDeniedError, ServerError
from ai.backend.client.v2.registry import BackendAIClientRegistry
from ai.backend.common.dto.manager.container_registry.request import (
    HarborWebhookRequestModel,
    PatchContainerRegistryRequestModel,
)
from ai.backend.common.dto.manager.container_registry.response import (
    PatchContainerRegistryResponseModel,
)


class TestContainerRegistryPatch:
    @pytest.mark.asyncio
    async def test_admin_patches_container_registry(
        self,
        admin_registry: BackendAIClientRegistry,
        container_registry_fixture: uuid.UUID,
    ) -> None:
        result = await admin_registry.container_registry.patch(
            str(container_registry_fixture),
            PatchContainerRegistryRequestModel(ssl_verify=False),
        )
        assert isinstance(result, PatchContainerRegistryResponseModel)
        assert result.id == container_registry_fixture
        assert result.ssl_verify is False

    @pytest.mark.asyncio
    async def test_regular_user_cannot_patch_registry(
        self,
        user_registry: BackendAIClientRegistry,
        container_registry_fixture: uuid.UUID,
    ) -> None:
        with pytest.raises(PermissionDeniedError):
            await user_registry.container_registry.patch(
                str(container_registry_fixture),
                PatchContainerRegistryRequestModel(ssl_verify=False),
            )


class TestContainerRegistryHarborWebhook:
    @pytest.mark.asyncio
    async def test_handle_harbor_webhook(
        self,
        admin_registry: BackendAIClientRegistry,
        harbor_registry_fixture: uuid.UUID,
    ) -> None:
        """A PULL_ARTIFACT event is gracefully ignored (no actual image scan triggered)."""
        request = HarborWebhookRequestModel(
            type="PULL_ARTIFACT",
            event_data=HarborWebhookRequestModel.EventData(
                resources=[
                    HarborWebhookRequestModel.EventData.Resource(
                        resource_url="harbor.test.local/testproject/testimage:latest",
                        tag="latest",
                    )
                ],
                repository=HarborWebhookRequestModel.EventData.Repository(
                    namespace="testproject",
                    name="testimage",
                ),
            ),
        )
        await admin_registry.container_registry.handle_harbor_webhook(request)

    @pytest.mark.asyncio
    async def test_harbor_webhook_with_nonexistent_registry(
        self,
        admin_registry: BackendAIClientRegistry,
    ) -> None:
        """Webhook with resource_url not matching any registry row raises ServerError."""
        request = HarborWebhookRequestModel(
            type="PULL_ARTIFACT",
            event_data=HarborWebhookRequestModel.EventData(
                resources=[
                    HarborWebhookRequestModel.EventData.Resource(
                        resource_url="nonexistent.registry.invalid/project/image:latest",
                        tag="latest",
                    )
                ],
                repository=HarborWebhookRequestModel.EventData.Repository(
                    namespace="project",
                    name="image",
                ),
            ),
        )
        with pytest.raises(ServerError):
            await admin_registry.container_registry.handle_harbor_webhook(request)
