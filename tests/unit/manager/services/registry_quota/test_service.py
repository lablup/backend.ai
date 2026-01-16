"""
Mock-based unit tests for RegistryQuotaService.

Tests verify service layer business logic using mocked repositories and clients.
"""

from __future__ import annotations

import uuid
from unittest.mock import AsyncMock, MagicMock

import pytest

from ai.backend.common.container_registry import ContainerRegistryType
from ai.backend.manager.clients.container_registry.harbor import (
    AbstractPerProjectRegistryQuotaClient,
    HarborAuthArgs,
    HarborProjectInfo,
)
from ai.backend.manager.repositories.registry_quota.repository import (
    AbstractRegistryQuotaRepository,
    ContainerRegistryRowInfo,
)
from ai.backend.manager.services.registry_quota.actions.create_registry_quota import (
    CreateRegistryQuotaAction,
)
from ai.backend.manager.services.registry_quota.actions.delete_registry_quota import (
    DeleteRegistryQuotaAction,
)
from ai.backend.manager.services.registry_quota.actions.read_registry_quota import (
    ReadRegistryQuotaAction,
)
from ai.backend.manager.services.registry_quota.actions.update_registry_quota import (
    UpdateRegistryQuotaAction,
)
from ai.backend.manager.services.registry_quota.service import (
    RegistryQuotaClientPool,
    RegistryQuotaService,
)


class TestCreateRegistryQuota:
    """Tests for RegistryQuotaService.create_registry_quota"""

    @pytest.fixture
    def mock_repository(self) -> MagicMock:
        return MagicMock(spec=AbstractRegistryQuotaRepository)

    @pytest.fixture
    def mock_client(self) -> MagicMock:
        mock = MagicMock(spec=AbstractPerProjectRegistryQuotaClient)
        mock.create_quota = AsyncMock()
        return mock

    @pytest.fixture
    def sample_registry_info(self) -> ContainerRegistryRowInfo:
        return ContainerRegistryRowInfo(
            id=uuid.uuid4(),
            url="https://harbor.example.com",
            registry_name="harbor",
            type=ContainerRegistryType.HARBOR2,
            project="test-project",
            username="admin",
            password="secret",
            ssl_verify=True,
            is_global=False,
            extra={},
        )

    @pytest.fixture
    def service(
        self,
        mock_repository: MagicMock,
        mock_client: MagicMock,
        sample_registry_info: ContainerRegistryRowInfo,
    ) -> RegistryQuotaService:
        mock_repository.fetch_container_registry_row = AsyncMock(
            return_value=sample_registry_info
        )
        service = RegistryQuotaService(repository=mock_repository)
        service._client_pool = MagicMock(spec=RegistryQuotaClientPool)
        service._client_pool.make_client = MagicMock(return_value=mock_client)
        return service

    async def test_create_registry_quota_success(
        self,
        service: RegistryQuotaService,
        mock_repository: MagicMock,
        mock_client: MagicMock,
    ) -> None:
        """Create registry quota should call client with correct params."""
        project_id = uuid.uuid4()
        quota = 1024

        action = CreateRegistryQuotaAction(project_id=project_id, quota=quota)
        result = await service.create_registry_quota(action)

        assert result.project_id == project_id
        mock_repository.fetch_container_registry_row.assert_called_once()
        mock_client.create_quota.assert_called_once()


class TestReadRegistryQuota:
    """Tests for RegistryQuotaService.read_registry_quota"""

    @pytest.fixture
    def mock_repository(self) -> MagicMock:
        return MagicMock(spec=AbstractRegistryQuotaRepository)

    @pytest.fixture
    def mock_client(self) -> MagicMock:
        mock = MagicMock(spec=AbstractPerProjectRegistryQuotaClient)
        mock.read_quota = AsyncMock(return_value=2048)
        return mock

    @pytest.fixture
    def sample_registry_info(self) -> ContainerRegistryRowInfo:
        return ContainerRegistryRowInfo(
            id=uuid.uuid4(),
            url="https://harbor.example.com",
            registry_name="harbor",
            type=ContainerRegistryType.HARBOR2,
            project="test-project",
            username="admin",
            password="secret",
            ssl_verify=True,
            is_global=False,
            extra={},
        )

    @pytest.fixture
    def service(
        self,
        mock_repository: MagicMock,
        mock_client: MagicMock,
        sample_registry_info: ContainerRegistryRowInfo,
    ) -> RegistryQuotaService:
        mock_repository.fetch_container_registry_row = AsyncMock(
            return_value=sample_registry_info
        )
        service = RegistryQuotaService(repository=mock_repository)
        service._client_pool = MagicMock(spec=RegistryQuotaClientPool)
        service._client_pool.make_client = MagicMock(return_value=mock_client)
        return service

    async def test_read_registry_quota_success(
        self,
        service: RegistryQuotaService,
        mock_repository: MagicMock,
        mock_client: MagicMock,
    ) -> None:
        """Read registry quota should return quota value."""
        project_id = uuid.uuid4()

        action = ReadRegistryQuotaAction(project_id=project_id)
        result = await service.read_registry_quota(action)

        assert result.project_id == project_id
        assert result.quota == 2048
        mock_repository.fetch_container_registry_row.assert_called_once()
        mock_client.read_quota.assert_called_once()


class TestUpdateRegistryQuota:
    """Tests for RegistryQuotaService.update_registry_quota"""

    @pytest.fixture
    def mock_repository(self) -> MagicMock:
        return MagicMock(spec=AbstractRegistryQuotaRepository)

    @pytest.fixture
    def mock_client(self) -> MagicMock:
        mock = MagicMock(spec=AbstractPerProjectRegistryQuotaClient)
        mock.update_quota = AsyncMock()
        return mock

    @pytest.fixture
    def sample_registry_info(self) -> ContainerRegistryRowInfo:
        return ContainerRegistryRowInfo(
            id=uuid.uuid4(),
            url="https://harbor.example.com",
            registry_name="harbor",
            type=ContainerRegistryType.HARBOR2,
            project="test-project",
            username="admin",
            password="secret",
            ssl_verify=True,
            is_global=False,
            extra={},
        )

    @pytest.fixture
    def service(
        self,
        mock_repository: MagicMock,
        mock_client: MagicMock,
        sample_registry_info: ContainerRegistryRowInfo,
    ) -> RegistryQuotaService:
        mock_repository.fetch_container_registry_row = AsyncMock(
            return_value=sample_registry_info
        )
        service = RegistryQuotaService(repository=mock_repository)
        service._client_pool = MagicMock(spec=RegistryQuotaClientPool)
        service._client_pool.make_client = MagicMock(return_value=mock_client)
        return service

    async def test_update_registry_quota_success(
        self,
        service: RegistryQuotaService,
        mock_repository: MagicMock,
        mock_client: MagicMock,
    ) -> None:
        """Update registry quota should call client with correct params."""
        project_id = uuid.uuid4()
        quota = 4096

        action = UpdateRegistryQuotaAction(project_id=project_id, quota=quota)
        result = await service.update_registry_quota(action)

        assert result.project_id == project_id
        mock_repository.fetch_container_registry_row.assert_called_once()
        mock_client.update_quota.assert_called_once()


class TestDeleteRegistryQuota:
    """Tests for RegistryQuotaService.delete_registry_quota"""

    @pytest.fixture
    def mock_repository(self) -> MagicMock:
        return MagicMock(spec=AbstractRegistryQuotaRepository)

    @pytest.fixture
    def mock_client(self) -> MagicMock:
        mock = MagicMock(spec=AbstractPerProjectRegistryQuotaClient)
        mock.delete_quota = AsyncMock()
        return mock

    @pytest.fixture
    def sample_registry_info(self) -> ContainerRegistryRowInfo:
        return ContainerRegistryRowInfo(
            id=uuid.uuid4(),
            url="https://harbor.example.com",
            registry_name="harbor",
            type=ContainerRegistryType.HARBOR2,
            project="test-project",
            username="admin",
            password="secret",
            ssl_verify=True,
            is_global=False,
            extra={},
        )

    @pytest.fixture
    def service(
        self,
        mock_repository: MagicMock,
        mock_client: MagicMock,
        sample_registry_info: ContainerRegistryRowInfo,
    ) -> RegistryQuotaService:
        mock_repository.fetch_container_registry_row = AsyncMock(
            return_value=sample_registry_info
        )
        service = RegistryQuotaService(repository=mock_repository)
        service._client_pool = MagicMock(spec=RegistryQuotaClientPool)
        service._client_pool.make_client = MagicMock(return_value=mock_client)
        return service

    async def test_delete_registry_quota_success(
        self,
        service: RegistryQuotaService,
        mock_repository: MagicMock,
        mock_client: MagicMock,
    ) -> None:
        """Delete registry quota should call client."""
        project_id = uuid.uuid4()

        action = DeleteRegistryQuotaAction(project_id=project_id)
        result = await service.delete_registry_quota(action)

        assert result.project_id == project_id
        mock_repository.fetch_container_registry_row.assert_called_once()
        mock_client.delete_quota.assert_called_once()
