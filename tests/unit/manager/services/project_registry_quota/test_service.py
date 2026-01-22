"""
Mock-based unit tests for ProjectRegistryQuotaService.

Tests verify service layer business logic using mocked repositories and clients.
"""

from __future__ import annotations

import uuid
from unittest.mock import AsyncMock, MagicMock, patch

import pytest

from ai.backend.common.container_registry import ContainerRegistryType
from ai.backend.manager.clients.container_registry.harbor import (
    AbstractPerProjectRegistryQuotaClient,
)
from ai.backend.manager.repositories.project_registry_quota.repository import (
    AbstractProjectRegistryQuotaRepository,
    ContainerRegistryRowInfo,
)
from ai.backend.manager.services.project_registry_quota.actions.create_project_registry_quota import (
    CreateProjectRegistryQuotaAction,
)
from ai.backend.manager.services.project_registry_quota.actions.delete_project_registry_quota import (
    DeleteProjectRegistryQuotaAction,
)
from ai.backend.manager.services.project_registry_quota.actions.read_project_registry_quota import (
    ReadProjectRegistryQuotaAction,
)
from ai.backend.manager.services.project_registry_quota.actions.update_project_registry_quota import (
    UpdateProjectRegistryQuotaAction,
)
from ai.backend.manager.services.project_registry_quota.service import (
    ProjectRegistryQuotaService,
)


class TestCreateProjectRegistryQuota:
    """Tests for ProjectRegistryQuotaService.create_project_registry_quota"""

    @pytest.fixture
    def mock_repository(self) -> MagicMock:
        return MagicMock(spec=AbstractProjectRegistryQuotaRepository)

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
        sample_registry_info: ContainerRegistryRowInfo,
    ) -> ProjectRegistryQuotaService:
        mock_repository.fetch_container_registry_row = AsyncMock(return_value=sample_registry_info)
        return ProjectRegistryQuotaService(repository=mock_repository)

    @pytest.mark.asyncio
    async def test_create_project_registry_quota_success(
        self,
        service: ProjectRegistryQuotaService,
        mock_repository: MagicMock,
        mock_client: MagicMock,
    ) -> None:
        """Create project registry quota should call client with correct params."""
        project_id = uuid.uuid4()
        quota = 1024

        with patch(
            "ai.backend.manager.services.project_registry_quota.service.make_project_registry_quota_client",
            return_value=mock_client,
        ):
            action = CreateProjectRegistryQuotaAction(project_id=project_id, quota=quota)
            result = await service.create_project_registry_quota(action)

        assert result.project_id == project_id
        mock_repository.fetch_container_registry_row.assert_called_once()
        mock_client.create_quota.assert_called_once()


class TestReadProjectRegistryQuota:
    """Tests for ProjectRegistryQuotaService.read_project_registry_quota"""

    @pytest.fixture
    def mock_repository(self) -> MagicMock:
        return MagicMock(spec=AbstractProjectRegistryQuotaRepository)

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
        sample_registry_info: ContainerRegistryRowInfo,
    ) -> ProjectRegistryQuotaService:
        mock_repository.fetch_container_registry_row = AsyncMock(return_value=sample_registry_info)
        return ProjectRegistryQuotaService(repository=mock_repository)

    @pytest.mark.asyncio
    async def test_read_project_registry_quota_success(
        self,
        service: ProjectRegistryQuotaService,
        mock_repository: MagicMock,
        mock_client: MagicMock,
    ) -> None:
        """Read project registry quota should return quota value."""
        project_id = uuid.uuid4()

        with patch(
            "ai.backend.manager.services.project_registry_quota.service.make_project_registry_quota_client",
            return_value=mock_client,
        ):
            action = ReadProjectRegistryQuotaAction(project_id=project_id)
            result = await service.read_project_registry_quota(action)

        assert result.project_id == project_id
        assert result.quota == 2048
        mock_repository.fetch_container_registry_row.assert_called_once()
        mock_client.read_quota.assert_called_once()


class TestUpdateProjectRegistryQuota:
    """Tests for ProjectRegistryQuotaService.update_project_registry_quota"""

    @pytest.fixture
    def mock_repository(self) -> MagicMock:
        return MagicMock(spec=AbstractProjectRegistryQuotaRepository)

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
        sample_registry_info: ContainerRegistryRowInfo,
    ) -> ProjectRegistryQuotaService:
        mock_repository.fetch_container_registry_row = AsyncMock(return_value=sample_registry_info)
        return ProjectRegistryQuotaService(repository=mock_repository)

    @pytest.mark.asyncio
    async def test_update_project_registry_quota_success(
        self,
        service: ProjectRegistryQuotaService,
        mock_repository: MagicMock,
        mock_client: MagicMock,
    ) -> None:
        """Update project registry quota should call client with correct params."""
        project_id = uuid.uuid4()
        quota = 4096

        with patch(
            "ai.backend.manager.services.project_registry_quota.service.make_project_registry_quota_client",
            return_value=mock_client,
        ):
            action = UpdateProjectRegistryQuotaAction(project_id=project_id, quota=quota)
            result = await service.update_project_registry_quota(action)

        assert result.project_id == project_id
        mock_repository.fetch_container_registry_row.assert_called_once()
        mock_client.update_quota.assert_called_once()


class TestDeleteProjectRegistryQuota:
    """Tests for ProjectRegistryQuotaService.delete_project_registry_quota"""

    @pytest.fixture
    def mock_repository(self) -> MagicMock:
        return MagicMock(spec=AbstractProjectRegistryQuotaRepository)

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
        sample_registry_info: ContainerRegistryRowInfo,
    ) -> ProjectRegistryQuotaService:
        mock_repository.fetch_container_registry_row = AsyncMock(return_value=sample_registry_info)
        return ProjectRegistryQuotaService(repository=mock_repository)

    @pytest.mark.asyncio
    async def test_delete_project_registry_quota_success(
        self,
        service: ProjectRegistryQuotaService,
        mock_repository: MagicMock,
        mock_client: MagicMock,
    ) -> None:
        """Delete project registry quota should call client."""
        project_id = uuid.uuid4()

        with patch(
            "ai.backend.manager.services.project_registry_quota.service.make_project_registry_quota_client",
            return_value=mock_client,
        ):
            action = DeleteProjectRegistryQuotaAction(project_id=project_id)
            result = await service.delete_project_registry_quota(action)

        assert result.project_id == project_id
        mock_repository.fetch_container_registry_row.assert_called_once()
        mock_client.delete_quota.assert_called_once()
