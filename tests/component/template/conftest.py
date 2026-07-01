from __future__ import annotations

import uuid
from unittest.mock import AsyncMock, MagicMock

import pytest
import sqlalchemy as sa
from sqlalchemy.ext.asyncio.engine import AsyncEngine as SAEngine

from ai.backend.manager.actions.validators import ActionValidators
from ai.backend.manager.actions.validators.rbac import RBACValidators
from ai.backend.manager.api.rest.cluster_template.handler import ClusterTemplateHandler
from ai.backend.manager.api.rest.cluster_template.registry import register_cluster_template_routes
from ai.backend.manager.api.rest.routing import RouteRegistry
from ai.backend.manager.api.rest.session_template.handler import SessionTemplateHandler
from ai.backend.manager.api.rest.session_template.registry import register_session_template_routes
from ai.backend.manager.api.rest.template.registry import register_template_routes
from ai.backend.manager.api.rest.types import RouteDeps
from ai.backend.manager.config.provider import ManagerConfigProvider
from ai.backend.manager.dependencies.infrastructure.redis import ValkeyClients
from ai.backend.manager.models.group import GroupRow
from ai.backend.manager.models.storage import StorageSessionManager
from ai.backend.manager.models.utils import ExtendedAsyncSAEngine
from ai.backend.manager.repositories.group.repositories import GroupRepositories
from ai.backend.manager.repositories.group.repository import GroupRepository
from ai.backend.manager.repositories.template.repository import TemplateRepository
from ai.backend.manager.services.group.processors import GroupProcessors
from ai.backend.manager.services.group.service import GroupService
from ai.backend.manager.services.template.processors import TemplateProcessors
from ai.backend.manager.services.template.service import TemplateService


def _mock_action_validators() -> MagicMock:
    mock_rbac = MagicMock(spec=RBACValidators)
    mock_rbac.scope = AsyncMock()
    mock_rbac.single_entity = AsyncMock()
    mock_validators = MagicMock(spec=ActionValidators)
    mock_validators.rbac = mock_rbac
    return mock_validators


@pytest.fixture()
def template_processors(database_engine: ExtendedAsyncSAEngine) -> TemplateProcessors:
    repo = TemplateRepository(database_engine)
    service = TemplateService(repository=repo)
    return TemplateProcessors(
        service=service, action_monitors=[], validators=_mock_action_validators()
    )


@pytest.fixture()
def group_processors(
    database_engine: ExtendedAsyncSAEngine,
    config_provider: ManagerConfigProvider,
    valkey_clients: ValkeyClients,
    storage_manager: StorageSessionManager,
) -> GroupProcessors:
    group_repo = GroupRepository(
        database_engine, config_provider, valkey_clients.stat, storage_manager
    )
    group_repos = GroupRepositories(repository=group_repo)
    service = GroupService(storage_manager, config_provider, valkey_clients.stat, group_repos)
    return GroupProcessors(
        group_service=service, action_monitors=[], validators=_mock_action_validators()
    )


@pytest.fixture()
def server_module_registries(
    route_deps: RouteDeps,
    template_processors: TemplateProcessors,
    group_processors: GroupProcessors,
) -> list[RouteRegistry]:
    """Load only the modules required for template-domain tests."""
    session_tpl_registry = register_session_template_routes(
        SessionTemplateHandler(template=template_processors, group=group_processors),
        route_deps,
    )
    cluster_tpl_registry = register_cluster_template_routes(
        ClusterTemplateHandler(template=template_processors, group=group_processors),
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
            sa.select(GroupRow.__table__.c.name).where(GroupRow.__table__.c.id == group_fixture)
        )
        row = result.first()
        assert row is not None
        return str(row[0])
