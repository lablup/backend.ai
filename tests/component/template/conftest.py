from __future__ import annotations

import secrets
import uuid
from collections.abc import AsyncIterator
from typing import TYPE_CHECKING, Any

import pytest
import sqlalchemy as sa
from sqlalchemy.ext.asyncio.engine import AsyncEngine as SAEngine

from ai.backend.common.data.entity.project import ProjectEntityType
from ai.backend.common.data.entity.session_template import SessionTemplateEntityType
from ai.backend.manager.actions.registry.registry import ProcessorRegistry
from ai.backend.manager.actions.registry.types import GroupMeta
from ai.backend.manager.api.rest.cluster_template.handler import ClusterTemplateHandler
from ai.backend.manager.api.rest.cluster_template.registry import register_cluster_template_routes
from ai.backend.manager.api.rest.routing import RouteRegistry
from ai.backend.manager.api.rest.session_template.handler import SessionTemplateHandler
from ai.backend.manager.api.rest.session_template.registry import register_session_template_routes
from ai.backend.manager.api.rest.template.registry import register_template_routes
from ai.backend.manager.api.rest.types import RouteDeps
from ai.backend.manager.clients.storage_proxy.session_manager import StorageSessionManager
from ai.backend.manager.config.provider import ManagerConfigProvider
from ai.backend.manager.dependencies.infrastructure.redis import ValkeyClients
from ai.backend.manager.models.project import ProjectRow
from ai.backend.manager.models.session_template.row import SessionTemplateRow, TemplateType
from ai.backend.manager.models.utils import ExtendedAsyncSAEngine
from ai.backend.manager.repositories.ops.v2.provider import V2DBOpsProvider
from ai.backend.manager.repositories.ops.v2.resource_policy.provider import (
    ResourcePolicyOpsProvider,
)
from ai.backend.manager.repositories.ops.v2.share.provider import ShareOpsProvider
from ai.backend.manager.repositories.project.repositories import ProjectRepositories
from ai.backend.manager.repositories.project.repository import ProjectRepository
from ai.backend.manager.repositories.template.repository import TemplateRepository
from ai.backend.manager.services.project.processors import ProjectProcessors
from ai.backend.manager.services.project.service import ProjectService
from ai.backend.manager.services.template.processors import TemplateProcessors
from ai.backend.manager.services.template.service import TemplateService
from ai.backend.testutils.fixtures import DomainFixtureData

if TYPE_CHECKING:
    from tests.component.conftest import UserFixtureData


@pytest.fixture()
def template_processors(
    database_engine: ExtendedAsyncSAEngine, processor_registry: ProcessorRegistry[Any]
) -> TemplateProcessors:
    repo = TemplateRepository(database_engine, ShareOpsProvider(database_engine))
    service = TemplateService(repository=repo)
    return TemplateProcessors(
        processor_registry.group(GroupMeta(SessionTemplateEntityType())), service
    )


@pytest.fixture()
def project_processors(
    database_engine: ExtendedAsyncSAEngine,
    config_provider: ManagerConfigProvider,
    valkey_clients: ValkeyClients,
    storage_manager: StorageSessionManager,
    processor_registry: ProcessorRegistry[Any],
) -> ProjectProcessors:
    group_repo = ProjectRepository(
        database_engine,
        V2DBOpsProvider(database_engine),
        ResourcePolicyOpsProvider(database_engine),
        config_provider,
        valkey_clients.stat,
        storage_manager,
    )
    group_repos = ProjectRepositories(repository=group_repo)
    service = ProjectService(storage_manager, config_provider, valkey_clients.stat, group_repos)
    return ProjectProcessors(processor_registry.group(GroupMeta(ProjectEntityType())), service)


@pytest.fixture()
def server_module_registries(
    route_deps: RouteDeps,
    template_processors: TemplateProcessors,
    project_processors: ProjectProcessors,
) -> list[RouteRegistry]:
    """Load only the modules required for template-domain tests."""
    session_tpl_registry = register_session_template_routes(
        SessionTemplateHandler(template=template_processors, project=project_processors),
        route_deps,
    )
    cluster_tpl_registry = register_cluster_template_routes(
        ClusterTemplateHandler(template=template_processors, project=project_processors),
        route_deps,
    )
    return [
        register_template_routes(
            route_deps, sub_registries=[session_tpl_registry, cluster_tpl_registry]
        ),
    ]


@pytest.fixture()
async def group_name_fixture(
    db_engine: SAEngine,
    group_fixture: uuid.UUID,
) -> str:
    """Query the group name from the database for the test group."""
    async with db_engine.begin() as conn:
        result = await conn.execute(
            sa.select(ProjectRow.__table__.c.name).where(ProjectRow.__table__.c.id == group_fixture)
        )
        row = result.first()
        assert row is not None
        return str(row[0])


@pytest.fixture()
async def task_template_id_in_a_project_nobody_joined(
    db_engine: SAEngine,
    domain_fixture: DomainFixtureData,
    resource_policy_fixture: str,
    admin_user_fixture: UserFixtureData,
) -> AsyncIterator[str]:
    project_id = uuid.uuid4()
    template_id = uuid.uuid4()
    async with db_engine.begin() as conn:
        await conn.execute(
            sa.insert(ProjectRow.__table__).values(
                id=project_id,
                name=f"group-{secrets.token_hex(6)}",
                is_active=True,
                domain_name=domain_fixture.domain_name,
                resource_policy=resource_policy_fixture,
            )
        )
        await conn.execute(
            sa.insert(SessionTemplateRow.__table__).values(
                id=template_id,
                is_active=True,
                domain_name=domain_fixture.domain_name,
                group_id=project_id,
                user_uuid=admin_user_fixture.user_uuid,
                type=TemplateType.TASK,
                name="in-a-project-nobody-joined",
                template={"apiVersion": "v1", "kind": "taskTemplate"},
            )
        )
    yield template_id.hex
    async with db_engine.begin() as conn:
        await conn.execute(
            SessionTemplateRow.__table__.delete().where(
                SessionTemplateRow.__table__.c.id == template_id
            )
        )
        await conn.execute(
            ProjectRow.__table__.delete().where(ProjectRow.__table__.c.id == project_id)
        )
