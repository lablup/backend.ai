from __future__ import annotations

import uuid
from unittest import mock
from unittest.mock import AsyncMock, MagicMock

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
    @pytest.mark.xfail(
        strict=True,
        reason=(
            "Client SDK v2 automatically adds an HMAC Authorization header to every request, "
            "but the harbor webhook endpoint validates it against "
            "registry.extra['webhook_auth_header']. "
            "Because the fixture does not populate that field, the header comparison always "
            "fails and the server returns 401 (container-registry_hook_unauthorized). "
            "This is a fundamental incompatibility between SDK auth and webhook auth; "
            "tracked separately for resolution."
        ),
    )
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
