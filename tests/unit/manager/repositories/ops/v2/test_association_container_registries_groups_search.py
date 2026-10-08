"""Registry/project associations use the standard search execution path."""

import uuid
from collections.abc import AsyncGenerator, Awaitable, Callable

import pytest

from ai.backend.common.container_registry import ContainerRegistryType
from ai.backend.common.data.entity.container_registry import ContainerRegistryID
from ai.backend.common.data.entity.project import ProjectID
from ai.backend.common.data.filter_specs import UUIDInMatchSpec
from ai.backend.common.types import ResourceSlot
from ai.backend.manager.data.container_registry.types import (
    AssociationContainerRegistriesGroupsData,
    ContainerRegistryData,
)
from ai.backend.manager.models.agent.row import AgentRow
from ai.backend.manager.models.association_container_registries_groups.row import (
    AssociationContainerRegistriesGroupsRow,
)
from ai.backend.manager.models.association_container_registries_groups.searchable_fields import (
    AssociationContainerRegistriesGroupsSearchableFields,
)
from ai.backend.manager.models.association_container_registries_groups.searchers import (
    AssociationContainerRegistriesGroupsSearcher,
)
from ai.backend.manager.models.container_registry.row import ContainerRegistryRow
from ai.backend.manager.models.domain.row import DomainRow
from ai.backend.manager.models.project.row import ProjectRow
from ai.backend.manager.models.resource_group.row import ResourceGroupForDomainRow
from ai.backend.manager.models.resource_policy.row import (
    ProjectResourcePolicyRow,
    UserResourcePolicyRow,
)
from ai.backend.manager.models.specs.pagination import NoPagination
from ai.backend.manager.models.specs.searcher import SearcherResult
from ai.backend.manager.models.user.row import UserRow
from ai.backend.manager.models.utils import ExtendedAsyncSAEngine
from ai.backend.manager.models.virtual_entity.virtual_entity import VirtualEntityRow
from ai.backend.manager.repositories.ops.v2.provider import V2DBOpsProvider
from ai.backend.testutils.db import with_tables
from ai.backend.testutils.fixtures import DomainFactory

# Register the ORM relationship cluster before SQLAlchemy configures the mappers.
_ORM_CLUSTER = (AgentRow, ResourceGroupForDomainRow)


class TestAssociationContainerRegistriesGroupsSearcher:
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
    def provider(self, database: ExtendedAsyncSAEngine) -> V2DBOpsProvider:
        return V2DBOpsProvider(database)

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
    async def project(self, project_factory: Callable[[], Awaitable[ProjectID]]) -> ProjectID:
        return await project_factory()

    @pytest.fixture
    async def another_project(
        self, project_factory: Callable[[], Awaitable[ProjectID]]
    ) -> ProjectID:
        return await project_factory()

    @pytest.fixture
    def association_factory(
        self, database: ExtendedAsyncSAEngine
    ) -> Callable[
        [ProjectID, ContainerRegistryID, bool], Awaitable[AssociationContainerRegistriesGroupsData]
    ]:
        async def create_association(
            project_id: ProjectID, registry_id: ContainerRegistryID, is_default: bool
        ) -> AssociationContainerRegistriesGroupsData:
            association = AssociationContainerRegistriesGroupsData(
                id=uuid.uuid4(),
                group_id=project_id,
                registry_id=registry_id,
                is_default=is_default,
            )
            async with database.begin_session() as session:
                session.add(
                    AssociationContainerRegistriesGroupsRow(
                        id=association.id,
                        group_id=association.group_id,
                        registry_id=association.registry_id,
                        is_default=association.is_default,
                    )
                )
            return association

        return create_association

    @pytest.fixture
    async def default_association(
        self,
        association_factory: Callable[
            [ProjectID, ContainerRegistryID, bool],
            Awaitable[AssociationContainerRegistriesGroupsData],
        ],
        project: ProjectID,
        default_registry: ContainerRegistryData,
    ) -> AssociationContainerRegistriesGroupsData:
        return await association_factory(project, default_registry.id, True)

    @pytest.fixture
    async def non_default_association(
        self,
        association_factory: Callable[
            [ProjectID, ContainerRegistryID, bool],
            Awaitable[AssociationContainerRegistriesGroupsData],
        ],
        project: ProjectID,
        same_name_registry: ContainerRegistryData,
    ) -> AssociationContainerRegistriesGroupsData:
        return await association_factory(project, same_name_registry.id, False)

    @pytest.fixture
    async def another_project_association(
        self,
        association_factory: Callable[
            [ProjectID, ContainerRegistryID, bool],
            Awaitable[AssociationContainerRegistriesGroupsData],
        ],
        another_project: ProjectID,
        default_registry: ContainerRegistryData,
    ) -> AssociationContainerRegistriesGroupsData:
        return await association_factory(another_project, default_registry.id, True)

    async def test_project_filter_returns_default_and_non_default_associations(
        self,
        provider: V2DBOpsProvider,
        project: ProjectID,
        default_association: AssociationContainerRegistriesGroupsData,
        non_default_association: AssociationContainerRegistriesGroupsData,
        another_project_association: AssociationContainerRegistriesGroupsData,
    ) -> None:
        async with provider.read_ops() as ops:
            found = await ops.search_in_global(
                AssociationContainerRegistriesGroupsSearcher(
                    pagination=NoPagination(),
                    conditions=[
                        AssociationContainerRegistriesGroupsSearchableFields.own.group_id.filter.in_(
                            UUIDInMatchSpec(negated=False, values=[project])
                        ),
                    ],
                )
            )
        assert {item.id: item for item in found.items} == {
            default_association.id: default_association,
            non_default_association.id: non_default_association,
        }
        assert found.total_count == 2
        assert not found.has_next_page and not found.has_previous_page

    @pytest.mark.parametrize("is_default", [True, False])
    async def test_default_filter(
        self,
        provider: V2DBOpsProvider,
        project: ProjectID,
        is_default: bool,
        default_association: AssociationContainerRegistriesGroupsData,
        non_default_association: AssociationContainerRegistriesGroupsData,
    ) -> None:
        async with provider.read_ops() as ops:
            found = await ops.search_in_global(
                AssociationContainerRegistriesGroupsSearcher(
                    pagination=NoPagination(),
                    conditions=[
                        AssociationContainerRegistriesGroupsSearchableFields.own.group_id.filter.in_(
                            UUIDInMatchSpec(negated=False, values=[project])
                        ),
                        AssociationContainerRegistriesGroupsSearchableFields.own.is_default.filter.equals(
                            is_default
                        ),
                    ],
                )
            )
        assert found == SearcherResult(
            items=[default_association if is_default else non_default_association],
            total_count=1,
            has_next_page=False,
            has_previous_page=False,
        )

    async def test_shared_registry_keeps_each_project_association(
        self,
        provider: V2DBOpsProvider,
        project: ProjectID,
        another_project: ProjectID,
        default_association: AssociationContainerRegistriesGroupsData,
        another_project_association: AssociationContainerRegistriesGroupsData,
    ) -> None:
        async with provider.read_ops() as ops:
            found = await ops.search_in_global(
                AssociationContainerRegistriesGroupsSearcher(
                    pagination=NoPagination(),
                    conditions=[
                        AssociationContainerRegistriesGroupsSearchableFields.own.group_id.filter.in_(
                            UUIDInMatchSpec(negated=False, values=[project, another_project])
                        ),
                        AssociationContainerRegistriesGroupsSearchableFields.own.is_default.filter.equals(
                            True
                        ),
                    ],
                )
            )
        assert {item.id: item for item in found.items} == {
            default_association.id: default_association,
            another_project_association.id: another_project_association,
        }
        assert found.total_count == 2
        assert not found.has_next_page and not found.has_previous_page

    async def test_project_without_association_returns_empty_result(
        self,
        provider: V2DBOpsProvider,
        project: ProjectID,
        another_project_association: AssociationContainerRegistriesGroupsData,
    ) -> None:
        async with provider.read_ops() as ops:
            found = await ops.search_in_global(
                AssociationContainerRegistriesGroupsSearcher(
                    pagination=NoPagination(),
                    conditions=[
                        AssociationContainerRegistriesGroupsSearchableFields.own.group_id.filter.in_(
                            UUIDInMatchSpec(negated=False, values=[project])
                        ),
                    ],
                )
            )
        assert found == SearcherResult(
            items=[], total_count=0, has_next_page=False, has_previous_page=False
        )

    async def test_empty_project_filter_returns_empty_result(
        self,
        provider: V2DBOpsProvider,
        default_association: AssociationContainerRegistriesGroupsData,
    ) -> None:
        async with provider.read_ops() as ops:
            found = await ops.search_in_global(
                AssociationContainerRegistriesGroupsSearcher(
                    pagination=NoPagination(),
                    conditions=[
                        AssociationContainerRegistriesGroupsSearchableFields.own.group_id.filter.in_(
                            UUIDInMatchSpec(negated=False, values=[])
                        ),
                    ],
                )
            )
        assert found == SearcherResult(
            items=[], total_count=0, has_next_page=False, has_previous_page=False
        )
