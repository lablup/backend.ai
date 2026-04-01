from __future__ import annotations

import uuid
from typing import Any
from unittest import mock
from unittest.mock import AsyncMock, MagicMock

import aiohttp
import pytest

from ai.backend.client.v2.exceptions import PermissionDeniedError, ServerError
from ai.backend.client.v2.registry import BackendAIClientRegistry
from ai.backend.common.container_registry import (
    ContainerRegistryType,
    CreateContainerRegistryRequestModel,
    ListContainerRegistriesResponseModel,
)
from ai.backend.common.dto.manager.container_registry.request import (
    HarborWebhookRequestModel,
    PatchContainerRegistryRequestModel,
)
from ai.backend.common.dto.manager.container_registry.response import (
    PatchContainerRegistryResponseModel,
)

# Must match HARBOR_WEBHOOK_AUTH_TOKEN in conftest.py
_HARBOR_WEBHOOK_AUTH_TOKEN = "test-harbor-webhook-token"


def _build_webhook_payload(
    event_type: str,
    project: str = "testproject",
    registry_host: str = "harbor-webhook.test.local",
    image_name: str = "testimage",
    tag: str = "latest",
) -> dict[str, Any]:
    return {
        "type": event_type,
        "event_data": {
            "resources": [
                {
                    "resource_url": f"{registry_host}/{project}/{image_name}:{tag}",
                    "tag": tag,
                }
            ],
            "repository": {
                "namespace": project,
                "name": image_name,
            },
        },
    }


class TestContainerRegistryCRUD:
    async def test_admin_creates_docker_registry(
        self,
        admin_registry: BackendAIClientRegistry,
    ) -> None:
        """Admin can create a DOCKER type registry; response contains correct fields."""
        result = await admin_registry.container_registry.create(
            CreateContainerRegistryRequestModel(
                url="https://docker-create.test.local",
                registry_name="test-create-docker",
                type=ContainerRegistryType.DOCKER,
            )
        )
        try:
            assert isinstance(result, PatchContainerRegistryResponseModel)
            assert result.url == "https://docker-create.test.local"
            assert result.registry_name == "test-create-docker"
            assert result.type == ContainerRegistryType.DOCKER
            assert result.id is not None
        finally:
            await admin_registry.container_registry.delete(str(result.id))

    async def test_admin_creates_harbor_registry(
        self,
        admin_registry: BackendAIClientRegistry,
    ) -> None:
        """Admin can create a HARBOR2 registry with project field set."""
        result = await admin_registry.container_registry.create(
            CreateContainerRegistryRequestModel(
                url="https://harbor-create.test.local",
                registry_name="test-create-harbor",
                type=ContainerRegistryType.HARBOR2,
                project="myproject",
            )
        )
        try:
            assert isinstance(result, PatchContainerRegistryResponseModel)
            assert result.url == "https://harbor-create.test.local"
            assert result.type == ContainerRegistryType.HARBOR2
            assert result.project == "myproject"
            assert result.id is not None
        finally:
            await admin_registry.container_registry.delete(str(result.id))

    async def test_admin_deletes_registry(
        self,
        admin_registry: BackendAIClientRegistry,
        container_registry_fixture: uuid.UUID,
    ) -> None:
        """Admin deletes a registry; it no longer appears in the list."""
        before = await admin_registry.container_registry.list_all()
        ids_before = [item.id for item in before.items]
        assert container_registry_fixture in ids_before

        await admin_registry.container_registry.delete(str(container_registry_fixture))

        after = await admin_registry.container_registry.list_all()
        ids_after = [item.id for item in after.items]
        assert container_registry_fixture not in ids_after

    async def test_admin_loads_registry_by_name(
        self,
        admin_registry: BackendAIClientRegistry,
        container_registry_fixture: uuid.UUID,
    ) -> None:
        """Admin can load a registry by registry_name."""
        all_registries = await admin_registry.container_registry.list_all()
        fixture_registry = next(
            r for r in all_registries.items if r.id == container_registry_fixture
        )
        registry_name = fixture_registry.registry_name
        assert registry_name is not None

        result = await admin_registry.container_registry.load(registry_name=registry_name)

        assert isinstance(result, ListContainerRegistriesResponseModel)
        assert len(result.items) >= 1
        found = next((r for r in result.items if r.id == container_registry_fixture), None)
        assert found is not None
        assert found.registry_name == registry_name

    async def test_admin_loads_harbor_registry_by_name_and_project(
        self,
        admin_registry: BackendAIClientRegistry,
        harbor_registry_fixture: uuid.UUID,
    ) -> None:
        """Admin can load a HARBOR2 registry filtered by registry_name and project."""
        all_registries = await admin_registry.container_registry.list_all()
        fixture_registry = next(r for r in all_registries.items if r.id == harbor_registry_fixture)
        registry_name = fixture_registry.registry_name
        assert registry_name is not None

        result = await admin_registry.container_registry.load(
            registry_name=registry_name, project="testproject"
        )

        assert isinstance(result, ListContainerRegistriesResponseModel)
        assert len(result.items) >= 1
        found = next((r for r in result.items if r.id == harbor_registry_fixture), None)
        assert found is not None
        assert found.project == "testproject"

    async def test_admin_lists_all_registries(
        self,
        admin_registry: BackendAIClientRegistry,
        container_registry_fixture: uuid.UUID,
        harbor_registry_fixture: uuid.UUID,
    ) -> None:
        """Admin can list all registries; both test registries are included."""
        result = await admin_registry.container_registry.list_all()

        assert isinstance(result, ListContainerRegistriesResponseModel)
        ids = [item.id for item in result.items]
        assert container_registry_fixture in ids
        assert harbor_registry_fixture in ids


class TestContainerRegistryPatch:
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


class TestContainerRegistryPermissions:
    async def test_regular_user_cannot_create_registry(
        self,
        user_registry: BackendAIClientRegistry,
    ) -> None:
        """Regular user (non-superadmin) gets PermissionDenied when creating a registry."""
        with pytest.raises(PermissionDeniedError):
            await user_registry.container_registry.create(
                CreateContainerRegistryRequestModel(
                    url="https://docker-user.test.local",
                    registry_name="test-user-create",
                    type=ContainerRegistryType.DOCKER,
                )
            )

    async def test_regular_user_cannot_delete_registry(
        self,
        user_registry: BackendAIClientRegistry,
        container_registry_fixture: uuid.UUID,
    ) -> None:
        """Regular user (non-superadmin) gets PermissionDenied when deleting a registry."""
        with pytest.raises(PermissionDeniedError):
            await user_registry.container_registry.delete(str(container_registry_fixture))


class TestContainerRegistryImageOperations:
    async def test_rescan_images(
        self,
        admin_registry: BackendAIClientRegistry,
        container_registry_fixture: uuid.UUID,
    ) -> None:
        """Admin triggers image rescan; operation completes without error (scanner mocked)."""
        all_registries = await admin_registry.container_registry.list_all()
        fixture_registry = next(
            r for r in all_registries.items if r.id == container_registry_fixture
        )
        registry_name = fixture_registry.registry_name
        assert registry_name is not None

        mock_scan_result = MagicMock()
        mock_scan_result.images = []
        mock_scan_result.errors = []

        mock_scanner = MagicMock()
        mock_scanner.rescan_single_registry = AsyncMock(return_value=mock_scan_result)

        mock_scanner_cls = MagicMock(return_value=mock_scanner)

        with mock.patch(
            "ai.backend.manager.services.container_registry.service.get_container_registry_cls",
            return_value=mock_scanner_cls,
        ):
            await admin_registry.container_registry.rescan_images(registry_name)

        mock_scanner_cls.assert_called_once()
        mock_scanner.rescan_single_registry.assert_awaited_once()

    async def test_clear_images(
        self,
        admin_registry: BackendAIClientRegistry,
        container_registry_fixture: uuid.UUID,
    ) -> None:
        """Admin clears images for a registry; operation completes without error."""
        all_registries = await admin_registry.container_registry.list_all()
        fixture_registry = next(
            r for r in all_registries.items if r.id == container_registry_fixture
        )
        registry_name = fixture_registry.registry_name
        assert registry_name is not None

        await admin_registry.container_registry.clear_images(registry_name)


class TestContainerRegistryHarborWebhook:
    async def test_push_artifact_with_valid_auth(
        self,
        server: Any,
        harbor_webhook_registry_fixture: uuid.UUID,
    ) -> None:
        """PUSH_ARTIFACT event with correct auth header → 204 (scan triggered)."""
        payload = _build_webhook_payload("PUSH_ARTIFACT")

        mock_scanner_cls = MagicMock()
        mock_scanner = MagicMock()
        mock_scanner.scan_single_ref = AsyncMock(return_value=None)
        mock_scanner_cls.return_value = mock_scanner

        with mock.patch(
            "ai.backend.manager.services.container_registry.service.HarborRegistry_v2",
            mock_scanner_cls,
        ):
            async with aiohttp.ClientSession() as session:
                resp = await session.post(
                    f"{server.url}/container-registries/webhook/harbor",
                    json=payload,
                    headers={"Authorization": _HARBOR_WEBHOOK_AUTH_TOKEN},
                )
            assert resp.status == 204

        mock_scanner.scan_single_ref.assert_awaited_once()

    async def test_push_artifact_with_invalid_auth(
        self,
        server: Any,
        harbor_webhook_registry_fixture: uuid.UUID,
    ) -> None:
        """PUSH_ARTIFACT event with wrong auth header → 401 unauthorized."""
        payload = _build_webhook_payload("PUSH_ARTIFACT")

        async with aiohttp.ClientSession() as session:
            resp = await session.post(
                f"{server.url}/container-registries/webhook/harbor",
                json=payload,
                headers={"Authorization": "wrong-token"},
            )
        assert resp.status == 401

    async def test_delete_artifact_event_ignored(
        self,
        server: Any,
        harbor_webhook_registry_fixture: uuid.UUID,
    ) -> None:
        """Non-PUSH_ARTIFACT event (DELETE_ARTIFACT) is silently ignored → 204."""
        payload = _build_webhook_payload("DELETE_ARTIFACT")

        async with aiohttp.ClientSession() as session:
            resp = await session.post(
                f"{server.url}/container-registries/webhook/harbor",
                json=payload,
                headers={"Authorization": _HARBOR_WEBHOOK_AUTH_TOKEN},
            )
        assert resp.status == 204

    async def test_webhook_for_nonexistent_registry(
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
