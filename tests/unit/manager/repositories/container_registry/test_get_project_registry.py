"""Tests for ContainerRegistryRepository.get_project_registry with a real database."""

from __future__ import annotations

import uuid
from collections.abc import AsyncGenerator
from dataclasses import dataclass

import pytest

from ai.backend.common.container_registry import ContainerRegistryType
from ai.backend.common.data.entity.container_registry import ContainerRegistryID
from ai.backend.common.types import ResourceSlot
from ai.backend.manager.data.container_registry.types import ContainerRegistryData
from ai.backend.manager.errors.image import ContainerRegistryNotFound
from ai.backend.manager.models.agent.row import AgentRow
from ai.backend.manager.models.association_container_registries_groups.row import (
    AssociationContainerRegistriesGroupsRow,
)

# ORM cluster registration: configure_mappers() (triggered when this isolated
# test registers a domain-cluster row) resolves string relationships against the
# registry. These rows are reachable via relationships but are not otherwise
# imported/registered by this test; _ORM_CLUSTER keeps them live.
from ai.backend.manager.models.container_registry.row import ContainerRegistryRow
from ai.backend.manager.models.domain.row import DomainRow
from ai.backend.manager.models.project.row import ProjectRow
from ai.backend.manager.models.rbac import ProjectScope
from ai.backend.manager.models.resource_group.row import ResourceGroupForDomainRow
from ai.backend.manager.models.resource_policy.row import (
    ProjectResourcePolicyRow,
    UserResourcePolicyRow,
)
from ai.backend.manager.models.user.row import UserRow
from ai.backend.manager.models.utils import ExtendedAsyncSAEngine
from ai.backend.manager.models.virtual_entity.virtual_entity import VirtualEntityRow
from ai.backend.manager.repositories.container_registry.repository import (
    ContainerRegistryRepository,
)
from ai.backend.manager.repositories.ops.v2.share.provider import ShareOpsProvider
from ai.backend.testutils.db import with_tables
from ai.backend.testutils.fixtures import DomainFactory, DomainFixtureData

_ORM_CLUSTER = (
    AgentRow,
    ResourceGroupForDomainRow,
)


@dataclass
class _ProjectWithRegistry:
    """A project (group) whose default registry is a container registry."""

    project_id: uuid.UUID
    registry_id: uuid.UUID
    registry_name: str
    project_name: str
    registry_url: str
    type: ContainerRegistryType
    username: str | None
    password: str | None
    ssl_verify: bool
    is_global: bool
    extra: dict[str, str] | None


@dataclass
class _ProjectWithoutRegistry:
    """A project (group) with no registry linked."""

    project_id: uuid.UUID


@dataclass
class _ProjectWithNonDefaultRegistry:
    """A project (group) allowed on a registry that is not its default registry."""

    project_id: uuid.UUID


class TestGetProjectRegistry:
    """Integration tests for get_project_registry using a real database."""

    @pytest.fixture
    async def db_with_cleanup(
        self,
        database_connection: ExtendedAsyncSAEngine,
    ) -> AsyncGenerator[ExtendedAsyncSAEngine, None]:
        async with with_tables(
            database_connection,
            [
                VirtualEntityRow,
                DomainRow,
                ProjectResourcePolicyRow,
                UserResourcePolicyRow,
                UserRow,
                ProjectRow,
                ContainerRegistryRow,
                AssociationContainerRegistriesGroupsRow,
            ],
        ):
            yield database_connection

    @pytest.fixture
    def repository(self, db_with_cleanup: ExtendedAsyncSAEngine) -> ContainerRegistryRepository:
        return ContainerRegistryRepository(db_with_cleanup, ShareOpsProvider(db_with_cleanup))

    @pytest.fixture
    async def sample_domain(
        self,
        domain_factory: DomainFactory,
        db_with_cleanup: ExtendedAsyncSAEngine,
    ) -> DomainFixtureData:
        """Pre-created domain for group tests."""
        return await domain_factory(db_with_cleanup)

    @pytest.fixture
    async def sample_resource_policy(
        self, db_with_cleanup: ExtendedAsyncSAEngine, sample_domain: DomainFixtureData
    ) -> str:
        """Pre-created resource policy. Returns policy name."""
        policy_name = f"test-policy-{sample_domain.domain_name}"
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
        sample_domain: DomainFixtureData,
        sample_resource_policy: str,
    ) -> _ProjectWithRegistry:
        """Pre-created project whose default registry is a ContainerRegistryRow."""
        registry_name = "harbor-" + str(uuid.uuid4())[:8] + ".example.com"
        registry_project = "project-" + str(uuid.uuid4())[:8]
        registry_type = ContainerRegistryType.HARBOR2
        registry_username = "test-user"
        registry_password = "test-pass"
        registry_ssl_verify = True
        registry_is_global = False
        registry_extra: dict[str, str] = {"key": "value"}

        async with db_with_cleanup.begin_session() as session:
            registry = ContainerRegistryRow(
                id=ContainerRegistryID(uuid.uuid4()),
                url=f"https://{registry_name}",
                registry_name=registry_name,
                type=registry_type,
                project=registry_project,
                username=registry_username,
                password=registry_password,
                ssl_verify=registry_ssl_verify,
                is_global=registry_is_global,
                extra=registry_extra,
            )
            session.add(registry)

            group = ProjectRow(
                name=f"test-group-{str(uuid.uuid4())[:8]}",
                domain_name=sample_domain.domain_name,
                total_resource_slots=ResourceSlot(),
                resource_policy=sample_resource_policy,
            )
            session.add(group)
            await session.flush()
            session.add(
                AssociationContainerRegistriesGroupsRow(
                    registry_id=registry.id, project_id=group.id, is_default=True
                )
            )
            project_id = group.id
            registry_id = registry.id
            await session.commit()

        return _ProjectWithRegistry(
            project_id=project_id,
            registry_id=registry_id,
            registry_name=registry_name,
            project_name=registry_project,
            registry_url=f"https://{registry_name}",
            type=registry_type,
            username=registry_username,
            password=registry_password,
            ssl_verify=registry_ssl_verify,
            is_global=registry_is_global,
            extra=registry_extra,
        )

    @pytest.fixture
    async def project_without_registry(
        self,
        db_with_cleanup: ExtendedAsyncSAEngine,
        sample_domain: DomainFixtureData,
        sample_resource_policy: str,
    ) -> _ProjectWithoutRegistry:
        """Pre-created project with no registry linked."""
        async with db_with_cleanup.begin_session() as session:
            group = ProjectRow(
                name=f"test-group-no-reg-{str(uuid.uuid4())[:8]}",
                domain_name=sample_domain.domain_name,
                total_resource_slots=ResourceSlot(),
                resource_policy=sample_resource_policy,
            )
            session.add(group)
            await session.flush()
            project_id = group.id
            await session.commit()

        return _ProjectWithoutRegistry(project_id=project_id)

    @pytest.fixture
    async def project_with_non_default_registry(
        self,
        db_with_cleanup: ExtendedAsyncSAEngine,
        sample_domain: DomainFixtureData,
        sample_resource_policy: str,
    ) -> _ProjectWithNonDefaultRegistry:
        """Pre-created project allowed on a registry without it being the default registry."""
        registry_name = "allowed-" + str(uuid.uuid4())[:8] + ".example.com"
        async with db_with_cleanup.begin_session() as session:
            registry = ContainerRegistryRow(
                id=ContainerRegistryID(uuid.uuid4()),
                url=f"https://{registry_name}",
                registry_name=registry_name,
                type=ContainerRegistryType.HARBOR2,
                project="project-" + str(uuid.uuid4())[:8],
            )
            session.add(registry)
            group = ProjectRow(
                name=f"test-group-allowed-{str(uuid.uuid4())[:8]}",
                domain_name=sample_domain.domain_name,
                total_resource_slots=ResourceSlot(),
                resource_policy=sample_resource_policy,
            )
            session.add(group)
            await session.flush()
            session.add(
                AssociationContainerRegistriesGroupsRow(
                    registry_id=registry.id, project_id=group.id, is_default=False
                )
            )
            project_id = group.id
            await session.commit()

        return _ProjectWithNonDefaultRegistry(project_id=project_id)

    @pytest.fixture
    async def project_with_minimal_registry(
        self,
        db_with_cleanup: ExtendedAsyncSAEngine,
        sample_domain: DomainFixtureData,
        sample_resource_policy: str,
    ) -> _ProjectWithRegistry:
        """Pre-created project with a registry that has only required fields (no username/password/extra)."""
        registry_name = "minimal-" + str(uuid.uuid4())[:8] + ".example.com"
        registry_project = "project-" + str(uuid.uuid4())[:8]
        registry_type = ContainerRegistryType.HARBOR2

        async with db_with_cleanup.begin_session() as session:
            registry = ContainerRegistryRow(
                id=ContainerRegistryID(uuid.uuid4()),
                url=f"https://{registry_name}",
                registry_name=registry_name,
                type=registry_type,
                project=registry_project,
            )
            session.add(registry)

            group = ProjectRow(
                name=f"test-group-minimal-{str(uuid.uuid4())[:8]}",
                domain_name=sample_domain.domain_name,
                total_resource_slots=ResourceSlot(),
                resource_policy=sample_resource_policy,
            )
            session.add(group)
            await session.flush()
            session.add(
                AssociationContainerRegistriesGroupsRow(
                    registry_id=registry.id, project_id=group.id, is_default=True
                )
            )
            project_id = group.id
            registry_id = registry.id
            await session.commit()

        return _ProjectWithRegistry(
            project_id=project_id,
            registry_id=registry_id,
            registry_name=registry_name,
            project_name=registry_project,
            registry_url=f"https://{registry_name}",
            type=registry_type,
            username=None,
            password=None,
            ssl_verify=True,
            is_global=True,
            extra=None,
        )

    async def test_get_project_registry_success(
        self,
        repository: ContainerRegistryRepository,
        project_with_registry: _ProjectWithRegistry,
    ) -> None:
        """Test successful fetch of the project's default registry."""
        # When
        scope_id = ProjectScope(project_id=project_with_registry.project_id)
        result = await repository.get_project_registry(scope_id)

        # Then
        assert isinstance(result, ContainerRegistryData)
        assert result.id == project_with_registry.registry_id
        assert result.url == project_with_registry.registry_url
        assert result.registry_name == project_with_registry.registry_name
        assert result.type == project_with_registry.type
        assert result.project == project_with_registry.project_name
        assert result.username == project_with_registry.username
        assert result.password == project_with_registry.password
        assert result.ssl_verify is project_with_registry.ssl_verify
        assert result.is_global is project_with_registry.is_global
        assert result.extra == project_with_registry.extra

    async def test_get_project_registry_project_not_found(
        self,
        repository: ContainerRegistryRepository,
    ) -> None:
        """Test ContainerRegistryNotFound when project does not exist."""
        scope_id = ProjectScope(project_id=uuid.uuid4())
        with pytest.raises(ContainerRegistryNotFound):
            await repository.get_project_registry(scope_id)

    async def test_get_project_registry_no_registry_config(
        self,
        repository: ContainerRegistryRepository,
        project_without_registry: _ProjectWithoutRegistry,
    ) -> None:
        """Test ContainerRegistryNotFound when no registry is linked to the project."""
        scope_id = ProjectScope(project_id=project_without_registry.project_id)
        with pytest.raises(ContainerRegistryNotFound):
            await repository.get_project_registry(scope_id)

    async def test_get_project_registry_not_default(
        self,
        repository: ContainerRegistryRepository,
        project_with_non_default_registry: _ProjectWithNonDefaultRegistry,
    ) -> None:
        """Test ContainerRegistryNotFound when the project's registry is not its default."""
        scope_id = ProjectScope(project_id=project_with_non_default_registry.project_id)
        with pytest.raises(ContainerRegistryNotFound):
            await repository.get_project_registry(scope_id)

    async def test_get_project_registry_with_minimal_fields(
        self,
        repository: ContainerRegistryRepository,
        project_with_minimal_registry: _ProjectWithRegistry,
    ) -> None:
        """Test fetch with registry that has only required fields (no username/password/extra)."""
        scope_id = ProjectScope(project_id=project_with_minimal_registry.project_id)
        result = await repository.get_project_registry(scope_id)

        assert result.username == project_with_minimal_registry.username
        assert result.password == project_with_minimal_registry.password
        assert result.extra == project_with_minimal_registry.extra
        assert result.ssl_verify is project_with_minimal_registry.ssl_verify
        assert result.is_global is project_with_minimal_registry.is_global
