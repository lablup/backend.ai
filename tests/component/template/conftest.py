from __future__ import annotations

import uuid

import pytest
import sqlalchemy as sa
from sqlalchemy.ext.asyncio.engine import AsyncEngine as SAEngine

from ai.backend.manager.api.rest.auth.handler import AuthHandler
from ai.backend.manager.api.rest.auth.registry import register_auth_routes
from ai.backend.manager.api.rest.cluster_template.handler import ClusterTemplateHandler
from ai.backend.manager.api.rest.cluster_template.registry import register_cluster_template_routes
from ai.backend.manager.api.rest.routing import RouteRegistry
from ai.backend.manager.api.rest.session_template.handler import SessionTemplateHandler
from ai.backend.manager.api.rest.session_template.registry import register_session_template_routes
from ai.backend.manager.api.rest.template.registry import register_template_routes
from ai.backend.manager.api.rest.types import RouteDeps
from ai.backend.manager.models.group import GroupRow
from ai.backend.manager.models.utils import ExtendedAsyncSAEngine
from ai.backend.manager.repositories.template.repository import TemplateRepository
from ai.backend.manager.services.auth.processors import AuthProcessors
from ai.backend.manager.services.template.processors import TemplateProcessors
from ai.backend.manager.services.template.service import TemplateService


@pytest.fixture()
def template_processors(database_engine: ExtendedAsyncSAEngine) -> TemplateProcessors:
    repo = TemplateRepository(database_engine)
    service = TemplateService(repository=repo)
    return TemplateProcessors(service=service, action_monitors=[])


@pytest.fixture()
def server_module_registries(
    route_deps: RouteDeps,
    auth_processors: AuthProcessors,
    template_processors: TemplateProcessors,
) -> list[RouteRegistry]:
    """Load only the modules required for template-domain tests."""
    session_tpl_registry = register_session_template_routes(
        SessionTemplateHandler(template=template_processors), route_deps
    )
    cluster_tpl_registry = register_cluster_template_routes(
        ClusterTemplateHandler(template=template_processors), route_deps
    )
    return [
        register_auth_routes(AuthHandler(auth=auth_processors), route_deps),
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
