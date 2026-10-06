"""Default registry reads follow association IDs, independent of legacy JSON or names."""

import uuid
from collections.abc import AsyncGenerator
from dataclasses import dataclass

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


@dataclass(frozen=True)
class RegistryProjects:
    projects: tuple[ProjectID, ...]
    registries: tuple[ContainerRegistryData, ...]


@pytest.fixture
async def database(
    database_connection: ExtendedAsyncSAEngine,
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
async def configured_projects(
    database: ExtendedAsyncSAEngine, domain_factory: DomainFactory
) -> RegistryProjects:
    domain = await domain_factory(database)
    projects = tuple(ProjectID(uuid.uuid4()) for _ in range(4))
    registries = tuple(
        ContainerRegistryData(
            id=ContainerRegistryID(uuid.uuid4()),
            url=f"https://registry-{index}.example.com",
            registry_name="same-name",
            type=ContainerRegistryType.HARBOR2,
            project="same-registry-project",
            username=f"user-{index}",
            password=f"password-{index}",
            ssl_verify=True,
            is_global=False,
            extra={"index": index},
        )
        for index in range(2)
    )
    async with database.begin_session() as session:
        session.add(
            ProjectResourcePolicyRow(
                name="default-registry-test-policy",
                max_vfolder_count=0,
                max_quota_scope_size=-1,
                max_network_count=3,
            )
        )
        await session.flush()
        for index, project_id in enumerate(projects):
            session.add(
                ProjectRow(
                    id=project_id,
                    name=f"project-{index}",
                    domain_name=domain.domain_name,
                    resource_policy="default-registry-test-policy",
                    total_resource_slots=ResourceSlot(),
                    container_registry={"registry": "legacy-only", "project": "unrelated"},
                )
            )
        for registry in registries:
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
        await session.flush()
        for index, project_id in enumerate(projects[:3]):
            for registry_index, registry in enumerate(registries):
                session.add(
                    AssociationContainerRegistriesGroupsRow(
                        group_id=project_id,
                        registry_id=registry.id,
                        is_default=index == registry_index,
                    )
                )
    return RegistryProjects(projects, registries)


async def test_defaults_use_registry_ids_and_preserve_registry_data(
    database: ExtendedAsyncSAEngine, configured_projects: RegistryProjects
) -> None:
    async with ProjectRegistryOpsProvider(database).read_ops() as ops:
        found = await ops.default_registries(
            DefaultContainerRegistryQuery(configured_projects.projects)
        )
    assert found == dict(
        zip(configured_projects.projects[:2], configured_projects.registries, strict=True)
    )


async def test_only_requested_projects_are_returned(
    database: ExtendedAsyncSAEngine, configured_projects: RegistryProjects
) -> None:
    async with ProjectRegistryOpsProvider(database).read_ops() as ops:
        found = await ops.default_registries(
            DefaultContainerRegistryQuery([configured_projects.projects[1]])
        )
    assert found == {configured_projects.projects[1]: configured_projects.registries[1]}


async def test_missing_defaults_and_missing_projects_are_absent(
    database: ExtendedAsyncSAEngine, configured_projects: RegistryProjects
) -> None:
    async with ProjectRegistryOpsProvider(database).read_ops() as ops:
        found = await ops.default_registries(
            DefaultContainerRegistryQuery([
                *configured_projects.projects[2:],
                ProjectID(uuid.uuid4()),
            ])
        )
    assert found == {}


async def test_empty_request_returns_no_registries(database: ExtendedAsyncSAEngine) -> None:
    async with ProjectRegistryOpsProvider(database).read_ops() as ops:
        assert await ops.default_registries(DefaultContainerRegistryQuery([])) == {}
