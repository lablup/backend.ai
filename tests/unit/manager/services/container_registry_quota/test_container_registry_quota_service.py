from __future__ import annotations

from unittest.mock import AsyncMock, MagicMock
from uuid import uuid4

import pytest

from ai.backend.common.container_registry import ContainerRegistryType
from ai.backend.manager.data.container_registry.types import PerProjectContainerRegistryInfo
from ai.backend.manager.models.rbac import ProjectScope
from ai.backend.manager.repositories.container_registry_quota.repository import (
    PerProjectRegistryQuotaRepository,
)
from ai.backend.manager.services.container_registry_quota.actions.create_quota import (
    CreateQuotaAction,
)
from ai.backend.manager.services.container_registry_quota.actions.delete_quota import (
    DeleteQuotaAction,
)
from ai.backend.manager.services.container_registry_quota.actions.read_quota import (
    ReadQuotaAction,
)
from ai.backend.manager.services.container_registry_quota.actions.update_quota import (
    UpdateQuotaAction,
)
from ai.backend.manager.services.container_registry_quota.service import (
    ContainerRegistryQuotaService,
)


@pytest.fixture
def mock_client() -> AsyncMock:
    client = AsyncMock()
    client.read_quota.return_value = 2048
    return client


@pytest.fixture
def mock_repository(sample_registry_info: PerProjectContainerRegistryInfo) -> MagicMock:
    repo = MagicMock(spec=PerProjectRegistryQuotaRepository)
    repo.fetch_container_registry_row = AsyncMock(return_value=sample_registry_info)
    return repo


@pytest.fixture
def service(
    mock_repository: MagicMock,
    mock_client: AsyncMock,
    monkeypatch: pytest.MonkeyPatch,
) -> ContainerRegistryQuotaService:
    monkeypatch.setattr(
        "ai.backend.manager.services.container_registry_quota.service.make_registry_quota_client",
        MagicMock(return_value=mock_client),
    )
    return ContainerRegistryQuotaService(repository=mock_repository)


@pytest.fixture
def scope_id() -> ProjectScope:
    return ProjectScope(project_id=uuid4(), domain_name="default")


@pytest.fixture
def sample_registry_info() -> PerProjectContainerRegistryInfo:
    return PerProjectContainerRegistryInfo(
        id=uuid4(),
        url="https://harbor.example.com",
        registry_name="test-registry",
        type=ContainerRegistryType.HARBOR2,
        project="test-project",
        username="admin",
        password="secret",
        ssl_verify=True,
        is_global=False,
        extra={},
    )


async def test_create_quota(
    service: ContainerRegistryQuotaService,
    mock_client: AsyncMock,
    scope_id: ProjectScope,
) -> None:
    result = await service.create_quota(CreateQuotaAction(scope_id=scope_id, quota=1024))

    assert result.scope_id == scope_id
    mock_client.create_quota.assert_called_once()


async def test_update_quota(
    service: ContainerRegistryQuotaService,
    mock_client: AsyncMock,
    scope_id: ProjectScope,
) -> None:
    result = await service.update_quota(UpdateQuotaAction(scope_id=scope_id, quota=2048))

    assert result.scope_id == scope_id
    mock_client.update_quota.assert_called_once()


async def test_delete_quota(
    service: ContainerRegistryQuotaService,
    mock_client: AsyncMock,
    scope_id: ProjectScope,
) -> None:
    result = await service.delete_quota(DeleteQuotaAction(scope_id=scope_id))

    assert result.scope_id == scope_id
    mock_client.delete_quota.assert_called_once()


async def test_read_quota(
    service: ContainerRegistryQuotaService,
    mock_client: AsyncMock,
    scope_id: ProjectScope,
) -> None:
    result = await service.read_quota(ReadQuotaAction(scope_id=scope_id))

    assert result.scope_id == scope_id
    assert result.quota == 2048
    mock_client.read_quota.assert_called_once()
