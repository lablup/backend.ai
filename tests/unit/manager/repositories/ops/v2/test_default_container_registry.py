"""Default registry reads follow association IDs, independent of legacy JSON or names."""

import uuid
from collections.abc import AsyncGenerator, Awaitable, Callable

import pytest

from ai.backend.common.container_registry import ContainerRegistryType
from ai.backend.common.data.entity.container_registry import ContainerRegistryID
from ai.backend.common.data.entity.project import ProjectID
from ai.backend.common.types import ResourceSlot
from ai.backend.manager.data.container_registry.types import ContainerRegistryData
from ai.backend.manager.models.agent.row import AgentRow
from ai.backend.manager.models.association_container_registries_groups.queriers import (
    DefaultContainerRegistryQuery,
)
from ai.backend.manager.models.association_container_registries_groups.row import (
    AssociationContainerRegistriesGroupsRow,
)
from ai.backend.manager.models.container_registry.row import ContainerRegistryRow
from ai.backend.manager.models.domain.row import DomainRow
from ai.backend.manager.models.project.row import ProjectRow
from ai.backend.manager.models.resource_group.row import ResourceGroupForDomainRow
from ai.backend.manager.models.resource_policy.row import (
    ProjectResourcePolicyRow,
    UserResourcePolicyRow,
)
from ai.backend.manager.models.user.row import UserRow
from ai.backend.manager.models.utils import ExtendedAsyncSAEngine
from ai.backend.manager.models.virtual_entity.virtual_entity import VirtualEntityRow
from ai.backend.manager.repositories.ops.v2.project_registry.provider import (
    ProjectRegistryOpsProvider,
)
from ai.backend.testutils.db import with_tables
from ai.backend.testutils.fixtures import DomainFactory

# Register the ORM relationship cluster before SQLAlchemy configures the mappers.
_ORM_CLUSTER = (AgentRow, ResourceGroupForDomainRow)


class TestDefaultContainerRegistry:
    @pytest.fixture
    async def database(
        self, database_connection: ExtendedAsyncSAEngine
    ) -> AsyncGenerator[ExtendedAsyncSAEngine]:
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
    def provider(self, database: ExtendedAsyncSAEngine) -> ProjectRegistryOpsProvider:
        return ProjectRegistryOpsProvider(database)

    @pytest.fixture
    async def project_factory(
        self, database: ExtendedAsyncSAEngine, domain_factory: DomainFactory
    ) -> Callable[[], Awaitable[ProjectID]]:
        domain = await domain_factory(database)
        policy_name = "default-registry-test-policy"
        async with database.begin_session() as session:
            session.add(
                ProjectResourcePolicyRow(
                    name=policy_name,
                    max_vfolder_count=0,
                    max_quota_scope_size=-1,
                    max_network_count=3,
                )
            )

        async def create_project() -> ProjectID:
            project_id = ProjectID(uuid.uuid4())
            async with database.begin_session() as session:
                session.add(
                    ProjectRow(
                        id=project_id,
                        name=f"project-{project_id}",
                        domain_name=domain.domain_name,
                        resource_policy=policy_name,
                        total_resource_slots=ResourceSlot(),
                        container_registry={"registry": "legacy-only", "project": "unrelated"},
                    )
                )
            return project_id

        return create_project

    @pytest.fixture
    def registry_factory(
        self, database: ExtendedAsyncSAEngine
    ) -> Callable[[str], Awaitable[ContainerRegistryData]]:
        async def create_registry(label: str) -> ContainerRegistryData:
            registry = ContainerRegistryData(
                id=ContainerRegistryID(uuid.uuid4()),
                url=f"https://{label}.example.com",
                registry_name="same-name",
                type=ContainerRegistryType.HARBOR2,
                project="same-registry-project",
                username=f"user-{label}",
                password=f"password-{label}",
                ssl_verify=True,
                is_global=False,
                extra={"label": label},
            )
            async with database.begin_session() as session:
                session.add(
                    ContainerRegistryRow(
                        id=registry.id,
                        url=registry.url,
                        registry_name=registry.registry_name,
                        type=registry.type,
                        project=registry.project,
                        username=registry.username,
                        password=registry.password,
                        ssl_verify=registry.ssl_verify,
                        is_global=registry.is_global,
                        extra=registry.extra,
                    )
                )
            return registry

        return create_registry

    @pytest.fixture
    async def default_registry(
        self, registry_factory: Callable[[str], Awaitable[ContainerRegistryData]]
    ) -> ContainerRegistryData:
        return await registry_factory("default")

    @pytest.fixture
    async def same_name_registry(
        self, registry_factory: Callable[[str], Awaitable[ContainerRegistryData]]
    ) -> ContainerRegistryData:
        return await registry_factory("same-name")

    @pytest.fixture
    async def project_with_default(
        self,
        database: ExtendedAsyncSAEngine,
        project_factory: Callable[[], Awaitable[ProjectID]],
        default_registry: ContainerRegistryData,
        same_name_registry: ContainerRegistryData,
    ) -> ProjectID:
        project_id = await project_factory()
        async with database.begin_session() as session:
            session.add_all([
                AssociationContainerRegistriesGroupsRow(
                    group_id=project_id,
                    registry_id=default_registry.id,
                    is_default=True,
                ),
                AssociationContainerRegistriesGroupsRow(
                    group_id=project_id,
                    registry_id=same_name_registry.id,
                    is_default=False,
                ),
            ])
        return project_id

    @pytest.fixture
    async def another_project_with_default(
        self,
        database: ExtendedAsyncSAEngine,
        project_factory: Callable[[], Awaitable[ProjectID]],
        same_name_registry: ContainerRegistryData,
    ) -> ProjectID:
        project_id = await project_factory()
        async with database.begin_session() as session:
            session.add(
                AssociationContainerRegistriesGroupsRow(
                    group_id=project_id,
                    registry_id=same_name_registry.id,
                    is_default=True,
                )
            )
        return project_id

    @pytest.fixture
    async def project_with_access_only(
        self,
        database: ExtendedAsyncSAEngine,
        project_factory: Callable[[], Awaitable[ProjectID]],
        default_registry: ContainerRegistryData,
    ) -> ProjectID:
        project_id = await project_factory()
        async with database.begin_session() as session:
            session.add(
                AssociationContainerRegistriesGroupsRow(
                    group_id=project_id,
                    registry_id=default_registry.id,
                    is_default=False,
                )
            )
        return project_id

    @pytest.fixture
    async def project_without_access(
        self, project_factory: Callable[[], Awaitable[ProjectID]]
    ) -> ProjectID:
        return await project_factory()

    @pytest.fixture
    def missing_project(self) -> ProjectID:
        return ProjectID(uuid.uuid4())

    async def test_defaults_use_registry_ids_and_preserve_registry_data(
        self,
        provider: ProjectRegistryOpsProvider,
        project_with_default: ProjectID,
        another_project_with_default: ProjectID,
        default_registry: ContainerRegistryData,
        same_name_registry: ContainerRegistryData,
    ) -> None:
        async with provider.read_ops() as ops:
            found = await ops.default_registries(
                DefaultContainerRegistryQuery([
                    project_with_default,
                    another_project_with_default,
                ])
            )
        assert found == {
            project_with_default: default_registry,
            another_project_with_default: same_name_registry,
        }

    async def test_only_requested_projects_are_returned(
        self,
        provider: ProjectRegistryOpsProvider,
        project_with_default: ProjectID,
        another_project_with_default: ProjectID,
        default_registry: ContainerRegistryData,
    ) -> None:
        async with provider.read_ops() as ops:
            found = await ops.default_registries(
                DefaultContainerRegistryQuery([project_with_default])
            )
        assert found == {project_with_default: default_registry}

    async def test_access_without_default_returns_no_registry(
        self,
        provider: ProjectRegistryOpsProvider,
        project_with_access_only: ProjectID,
    ) -> None:
        async with provider.read_ops() as ops:
            found = await ops.default_registries(
                DefaultContainerRegistryQuery([project_with_access_only])
            )
        assert found == {}

    async def test_project_without_access_returns_no_registry(
        self,
        provider: ProjectRegistryOpsProvider,
        project_without_access: ProjectID,
    ) -> None:
        async with provider.read_ops() as ops:
            found = await ops.default_registries(
                DefaultContainerRegistryQuery([project_without_access])
            )
        assert found == {}

    async def test_missing_project_returns_no_registry(
        self,
        provider: ProjectRegistryOpsProvider,
        missing_project: ProjectID,
    ) -> None:
        async with provider.read_ops() as ops:
            found = await ops.default_registries(DefaultContainerRegistryQuery([missing_project]))
        assert found == {}

    async def test_empty_request_returns_no_registries(
        self,
        provider: ProjectRegistryOpsProvider,
    ) -> None:
        async with provider.read_ops() as ops:
            assert await ops.default_registries(DefaultContainerRegistryQuery([])) == {}
