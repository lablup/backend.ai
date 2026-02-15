from unittest.mock import AsyncMock, MagicMock

import pytest
from yarl import URL

from ai.backend.client.v2.base_client import BackendAIClient
from ai.backend.client.v2.config import ClientConfig
from ai.backend.client.v2.domains.container_registry import ContainerRegistryClient
from ai.backend.common.container_registry import (
    PatchContainerRegistryRequestModel,
    PatchContainerRegistryResponseModel,
)
from ai.backend.common.dto.manager.registry.request import HarborWebhookRequestModel

from .conftest import MockAuth

_DEFAULT_CONFIG = ClientConfig(endpoint=URL("https://api.example.com"))


def _make_request_session(resp: AsyncMock) -> MagicMock:
    mock_ctx = AsyncMock()
    mock_ctx.__aenter__ = AsyncMock(return_value=resp)
    mock_ctx.__aexit__ = AsyncMock(return_value=False)
    mock_session = MagicMock()
    mock_session.request = MagicMock(return_value=mock_ctx)
    return mock_session


def _make_client(mock_session: MagicMock) -> BackendAIClient:
    return BackendAIClient(_DEFAULT_CONFIG, MockAuth(), mock_session)


class TestContainerRegistryClient:
    @pytest.mark.asyncio
    async def test_patch_sends_correct_request(self) -> None:
        mock_resp = AsyncMock()
        mock_resp.status = 200
        mock_resp.json = AsyncMock(
            return_value={
                "url": "https://registry.example.com",
                "registry_name": "test-registry",
                "type": "harbor2",
            }
        )
        mock_session = _make_request_session(mock_resp)
        client = _make_client(mock_session)
        domain = ContainerRegistryClient(client)

        request = PatchContainerRegistryRequestModel(url="https://registry.example.com")
        result = await domain.patch("reg-123", request)

        assert isinstance(result, PatchContainerRegistryResponseModel)
        assert result.url == "https://registry.example.com"
        assert result.registry_name == "test-registry"

        call_args = mock_session.request.call_args
        assert call_args[0][0] == "PATCH"
        assert "/container-registries/reg-123" in str(call_args[0][1])

    @pytest.mark.asyncio
    async def test_patch_path_interpolation(self) -> None:
        mock_resp = AsyncMock()
        mock_resp.status = 200
        mock_resp.json = AsyncMock(return_value={"type": "docker"})
        mock_session = _make_request_session(mock_resp)
        client = _make_client(mock_session)
        domain = ContainerRegistryClient(client)

        request = PatchContainerRegistryRequestModel(ssl_verify=True)
        await domain.patch("my-special-id", request)

        call_args = mock_session.request.call_args
        url = str(call_args[0][1])
        assert "my-special-id" in url
        assert "container-registries" in url

    @pytest.mark.asyncio
    async def test_patch_serializes_request_body(self) -> None:
        mock_resp = AsyncMock()
        mock_resp.status = 200
        mock_resp.json = AsyncMock(return_value={})
        mock_session = _make_request_session(mock_resp)
        client = _make_client(mock_session)
        domain = ContainerRegistryClient(client)

        request = PatchContainerRegistryRequestModel(
            url="https://reg.io",
            username="user",
        )
        await domain.patch("r1", request)

        call_kwargs = mock_session.request.call_args.kwargs
        assert call_kwargs["json"]["url"] == "https://reg.io"
        assert call_kwargs["json"]["username"] == "user"


class TestHarborWebhook:
    @pytest.mark.asyncio
    async def test_handle_harbor_webhook_sends_post(self) -> None:
        mock_resp = AsyncMock()
        mock_resp.status = 204
        mock_session = _make_request_session(mock_resp)
        client = _make_client(mock_session)
        domain = ContainerRegistryClient(client)

        request = HarborWebhookRequestModel(
            type="PUSH_ARTIFACT",
            event_data=HarborWebhookRequestModel.EventData(
                resources=[
                    HarborWebhookRequestModel.EventData.Resource(
                        resource_url="https://harbor.example.com/library/nginx",
                        tag="latest",
                    ),
                ],
                repository=HarborWebhookRequestModel.EventData.Repository(
                    namespace="library",
                    name="nginx",
                ),
            ),
        )
        await domain.handle_harbor_webhook(request)

        call_args = mock_session.request.call_args
        assert call_args[0][0] == "POST"
        assert "/container-registries/webhook/harbor" in str(call_args[0][1])
        call_kwargs = call_args.kwargs
        assert call_kwargs["json"]["type"] == "PUSH_ARTIFACT"
        assert call_kwargs["json"]["event_data"]["repository"]["name"] == "nginx"
