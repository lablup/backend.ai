"""
Tests for PerProjectRegistryQuota repository functionality.
Tests the repository layer with real database operations.
"""

from __future__ import annotations

import uuid
from collections.abc import AsyncGenerator
from dataclasses import dataclass
from unittest.mock import MagicMock

import pytest

from ai.backend.common.container_registry import ContainerRegistryType
from ai.backend.common.types import ResourceSlot
from ai.backend.manager.data.container_registry.types import PerProjectContainerRegistryInfo
from ai.backend.manager.errors.image import ContainerRegistryNotFound
from ai.backend.manager.models.container_registry import ContainerRegistryRow
from ai.backend.manager.models.domain import DomainRow
from ai.backend.manager.models.group import GroupRow
from ai.backend.manager.models.rbac import ProjectScope
from ai.backend.manager.models.resource_policy import ProjectResourcePolicyRow
from ai.backend.manager.models.utils import ExtendedAsyncSAEngine
from ai.backend.manager.repositories.container_registry_quota.repositories import (
    PerProjectRegistryQuotaRepositories,
)
from ai.backend.manager.repositories.container_registry_quota.repository import (
    PerProjectRegistryQuotaRepository,
)
from ai.backend.manager.repositories.types import RepositoryArgs
from ai.backend.testutils.db import with_tables


@dataclass
class _ProjectWithRegistry:
    """A project (group) linked to a container registry via container_registry JSON."""

    project_id: uuid.UUID
    registry_id: uuid.UUID
    registry_name: str
    project_name: str
    registry_url: str


@dataclass
class _ProjectWithoutRegistry:
    """A project (group) with no container_registry JSON configured."""

    project_id: uuid.UUID


@dataclass
class _ProjectWithInvalidRegistry:
    """A project (group) with invalid container_registry JSON (missing keys)."""

    project_id: uuid.UUID


class TestPerProjectRegistryQuotaRepository:
    """Integration tests for PerProjectRegistryQuotaRepository using real database."""

    @pytest.fixture
    async def db_with_cleanup(
        self,
        database_connection: ExtendedAsyncSAEngine,
    ) -> AsyncGenerator[ExtendedAsyncSAEngine, None]:
        async with with_tables(
            database_connection,
            [
                DomainRow,
                ProjectResourcePolicyRow,
                GroupRow,
                ContainerRegistryRow,
            ],
        ):
            yield database_connection

    @pytest.fixture
    def repository(
        self, db_with_cleanup: ExtendedAsyncSAEngine
    ) -> PerProjectRegistryQuotaRepository:
        """Create PerProjectRegistryQuotaRepository instance with real database"""
        return PerProjectRegistryQuotaRepository(db_with_cleanup)

    @pytest.fixture
    async def sample_domain(self, db_with_cleanup: ExtendedAsyncSAEngine) -> str:
        """Pre-created domain for group tests. Returns domain name."""
        domain_name = "test-domain-" + str(uuid.uuid4())[:8]
        async with db_with_cleanup.begin_session() as session:
            domain = DomainRow(name=domain_name, total_resource_slots=ResourceSlot())
            session.add(domain)
            await session.commit()
        return domain_name

    @pytest.fixture
    async def sample_resource_policy(
        self, db_with_cleanup: ExtendedAsyncSAEngine, sample_domain: str
    ) -> str:
        """Pre-created resource policy. Returns policy name."""
        policy_name = f"test-policy-{sample_domain}"
        async with db_with_cleanup.begin_session() as session:
            project_policy = ProjectResourcePolicyRow(
                name=policy_name,
                max_vfolder_count=0,
                max_quota_scope_size=-1,
                max_network_count=3,
            )
            session.add(project_policy)
            await session.commit()
        return policy_name

    @pytest.fixture
    async def project_with_registry(
        self,
        db_with_cleanup: ExtendedAsyncSAEngine,
        sample_domain: str,
        sample_resource_policy: str,
    ) -> _ProjectWithRegistry:
        """Pre-created project with valid container_registry config linked to a ContainerRegistryRow."""
        registry_name = "harbor-" + str(uuid.uuid4())[:8] + ".example.com"
        registry_project = "project-" + str(uuid.uuid4())[:8]

        async with db_with_cleanup.begin_session() as session:
            registry = ContainerRegistryRow(
                id=uuid.uuid4(),
                url=f"https://{registry_name}",
                registry_name=registry_name,
                type=ContainerRegistryType.HARBOR2,
                project=registry_project,
                username="test-user",
                password="test-pass",
                ssl_verify=True,
                is_global=False,
                extra={"key": "value"},
            )
            session.add(registry)

            group = GroupRow(
                name=f"test-group-{str(uuid.uuid4())[:8]}",
                domain_name=sample_domain,
                total_resource_slots=ResourceSlot(),
                resource_policy=sample_resource_policy,
                container_registry={
                    "registry": registry_name,
                    "project": registry_project,
                },
            )
            session.add(group)
            await session.flush()
            project_id = group.id
            registry_id = registry.id
            await session.commit()

        return _ProjectWithRegistry(
            project_id=project_id,
            registry_id=registry_id,
            registry_name=registry_name,
            project_name=registry_project,
            registry_url=f"https://{registry_name}",
        )

    @pytest.fixture
    async def project_without_registry(
        self,
        db_with_cleanup: ExtendedAsyncSAEngine,
        sample_domain: str,
        sample_resource_policy: str,
    ) -> _ProjectWithoutRegistry:
        """Pre-created project with no container_registry configured."""
        async with db_with_cleanup.begin_session() as session:
            group = GroupRow(
                name=f"test-group-no-reg-{str(uuid.uuid4())[:8]}",
                domain_name=sample_domain,
                total_resource_slots=ResourceSlot(),
                resource_policy=sample_resource_policy,
                container_registry=None,
            )
            session.add(group)
            await session.flush()
            project_id = group.id
            await session.commit()

        return _ProjectWithoutRegistry(project_id=project_id)

    @pytest.fixture
    async def project_with_invalid_registry(
        self,
        db_with_cleanup: ExtendedAsyncSAEngine,
        sample_domain: str,
        sample_resource_policy: str,
    ) -> _ProjectWithInvalidRegistry:
        """Pre-created project with empty container_registry dict (missing required keys)."""
        async with db_with_cleanup.begin_session() as session:
            group = GroupRow(
                name=f"test-group-invalid-{str(uuid.uuid4())[:8]}",
                domain_name=sample_domain,
                total_resource_slots=ResourceSlot(),
                resource_policy=sample_resource_policy,
                container_registry={},
            )
            session.add(group)
            await session.flush()
            project_id = group.id
            await session.commit()

        return _ProjectWithInvalidRegistry(project_id=project_id)

    @pytest.mark.asyncio
    async def test_fetch_container_registry_row_success(
        self,
        repository: PerProjectRegistryQuotaRepository,
        project_with_registry: _ProjectWithRegistry,
    ) -> None:
        """Test successful fetch of registry info from a project with valid config."""
        # When
        scope_id = ProjectScope(project_id=project_with_registry.project_id)
        result = await repository.fetch_container_registry_row(scope_id)

        # Then
        assert isinstance(result, PerProjectContainerRegistryInfo)
        assert result.id == project_with_registry.registry_id
        assert result.url == project_with_registry.registry_url
        assert result.registry_name == project_with_registry.registry_name
        assert result.type == ContainerRegistryType.HARBOR2
        assert result.project == project_with_registry.project_name
        assert result.username == "test-user"
        assert result.password == "test-pass"
        assert result.ssl_verify is True
        assert result.is_global is False
        assert result.extra == {"key": "value"}

    @pytest.mark.asyncio
    async def test_fetch_container_registry_row_project_not_found(
        self,
        repository: PerProjectRegistryQuotaRepository,
    ) -> None:
        """Test ContainerRegistryNotFound when project does not exist."""
        scope_id = ProjectScope(project_id=uuid.uuid4())
        with pytest.raises(ContainerRegistryNotFound):
            await repository.fetch_container_registry_row(scope_id)

    @pytest.mark.asyncio
    async def test_fetch_container_registry_row_no_registry_config(
        self,
        repository: PerProjectRegistryQuotaRepository,
        project_without_registry: _ProjectWithoutRegistry,
    ) -> None:
        """Test ContainerRegistryNotFound when project has no container_registry config."""
        scope_id = ProjectScope(project_id=project_without_registry.project_id)
        with pytest.raises(ContainerRegistryNotFound):
            await repository.fetch_container_registry_row(scope_id)

    @pytest.mark.asyncio
    async def test_fetch_container_registry_row_invalid_registry_config(
        self,
        repository: PerProjectRegistryQuotaRepository,
        project_with_invalid_registry: _ProjectWithInvalidRegistry,
    ) -> None:
        """Test ContainerRegistryNotFound when config is empty dict (missing required keys)."""
        scope_id = ProjectScope(project_id=project_with_invalid_registry.project_id)
        with pytest.raises(ContainerRegistryNotFound):
            await repository.fetch_container_registry_row(scope_id)

    @pytest.mark.asyncio
    async def test_fetch_container_registry_row_registry_row_not_found(
        self,
        db_with_cleanup: ExtendedAsyncSAEngine,
        repository: PerProjectRegistryQuotaRepository,
        sample_domain: str,
        sample_resource_policy: str,
    ) -> None:
        """Test ContainerRegistryNotFound when config points to non-existent registry."""
        async with db_with_cleanup.begin_session() as session:
            group = GroupRow(
                name=f"test-group-orphan-{str(uuid.uuid4())[:8]}",
                domain_name=sample_domain,
                total_resource_slots=ResourceSlot(),
                resource_policy=sample_resource_policy,
                container_registry={
                    "registry": "non-existent-registry",
                    "project": "non-existent-project",
                },
            )
            session.add(group)
            await session.flush()
            project_id = group.id
            await session.commit()

        scope_id = ProjectScope(project_id=project_id)
        with pytest.raises(ContainerRegistryNotFound):
            await repository.fetch_container_registry_row(scope_id)

    @pytest.mark.asyncio
    async def test_fetch_registry_row_with_minimal_fields(
        self,
        db_with_cleanup: ExtendedAsyncSAEngine,
        repository: PerProjectRegistryQuotaRepository,
        sample_domain: str,
        sample_resource_policy: str,
    ) -> None:
        """Test fetch with registry that has only required fields (no username/password/extra)."""
        registry_name = "minimal-" + str(uuid.uuid4())[:8] + ".example.com"
        registry_project = "project-" + str(uuid.uuid4())[:8]

        async with db_with_cleanup.begin_session() as session:
            registry = ContainerRegistryRow(
                id=uuid.uuid4(),
                url=f"https://{registry_name}",
                registry_name=registry_name,
                type=ContainerRegistryType.HARBOR2,
                project=registry_project,
            )
            session.add(registry)

            group = GroupRow(
                name=f"test-group-minimal-{str(uuid.uuid4())[:8]}",
                domain_name=sample_domain,
                total_resource_slots=ResourceSlot(),
                resource_policy=sample_resource_policy,
                container_registry={
                    "registry": registry_name,
                    "project": registry_project,
                },
            )
            session.add(group)
            await session.flush()
            project_id = group.id
            await session.commit()

        scope_id = ProjectScope(project_id=project_id)
        result = await repository.fetch_container_registry_row(scope_id)

        # Verify fallback defaults for nullable text fields
        assert result.username == ""
        assert result.password == ""
        assert result.extra == {}
        # ssl_verify and is_global have server_default=true in the DB schema
        assert result.ssl_verify is True
        assert result.is_global is True


class TestPerProjectRegistryQuotaRepositories:
    """Tests for the PerProjectRegistryQuotaRepositories factory."""

    def test_create_builds_repository(self) -> None:
        """create() returns a Repositories instance containing a PerProjectRegistryQuotaRepository."""
        mock_db = MagicMock(spec=ExtendedAsyncSAEngine)
        args = MagicMock(spec=RepositoryArgs)
        args.db = mock_db

        repos = PerProjectRegistryQuotaRepositories.create(args)

        assert isinstance(repos, PerProjectRegistryQuotaRepositories)
        assert isinstance(repos.repository, PerProjectRegistryQuotaRepository)
