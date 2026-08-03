from __future__ import annotations

import uuid
from collections.abc import AsyncIterator
from typing import TYPE_CHECKING
from unittest.mock import MagicMock

import pytest
import sqlalchemy as sa
from sqlalchemy.ext.asyncio.engine import AsyncEngine as SAEngine

from ai.backend.common.data.app_config.types import AppConfigScopeType
from ai.backend.manager.api.adapters.app_config.adapter import AppConfigAdapter
from ai.backend.manager.api.rest.routing import RouteRegistry
from ai.backend.manager.api.rest.types import RouteDeps
from ai.backend.manager.api.rest.v2.app_config.handler import V2AppConfigHandler
from ai.backend.manager.api.rest.v2.app_config.registry import register_v2_app_config_routes
from ai.backend.manager.models.app_config_allow_list.row import AppConfigAllowListRow
from ai.backend.manager.models.app_config_definition.row import AppConfigDefinitionRow
from ai.backend.manager.models.app_config_fragment.row import AppConfigFragmentRow
from ai.backend.manager.models.utils import ExtendedAsyncSAEngine
from ai.backend.manager.repositories.app_config_fragment.repository import (
    AppConfigFragmentRepository,
)
from ai.backend.manager.repositories.ops.rbac.provider import RBACOpsProvider
from ai.backend.manager.services.app_config.processors import AppConfigProcessors
from ai.backend.manager.services.app_config.service import AppConfigService

if TYPE_CHECKING:
    from tests.component.conftest import UserFixtureData


@pytest.fixture()
def app_config_processors(database_engine: ExtendedAsyncSAEngine) -> AppConfigProcessors:
    """The real read path: no RBAC validator, since the adapter fills the principal itself."""
    repository = AppConfigFragmentRepository(RBACOpsProvider(database_engine))
    return AppConfigProcessors(service=AppConfigService(repository), action_monitors=[])


@pytest.fixture()
def app_config_adapter(app_config_processors: AppConfigProcessors) -> AppConfigAdapter:
    """``AppConfigAdapter`` reaches only ``self._processors.app_config``, so a MagicMock
    carrying the real processors on that attribute is enough."""
    processors = MagicMock()
    processors.app_config = app_config_processors
    return AppConfigAdapter(processors)


@pytest.fixture()
def server_module_registries(
    route_deps: RouteDeps,
    app_config_adapter: AppConfigAdapter,
) -> list[RouteRegistry]:
    v2_registry = RouteRegistry.create("v2", route_deps.cors_options)
    v2_registry.add_subregistry(
        register_v2_app_config_routes(V2AppConfigHandler(adapter=app_config_adapter), route_deps)
    )
    return [v2_registry]


@pytest.fixture()
async def merged_fragments(
    db_engine: SAEngine,
    regular_user_fixture: UserFixtureData,
) -> AsyncIterator[None]:
    """Registers two config names, each named after the role it plays in the tests.

    ``contributed`` is allow-listed at every scope and holds a public fragment the caller's
    own overrides; ``uncontributed`` is registered and allow-listed but holds no fragment
    anywhere, standing for a requested name nothing merges into.
    """
    config_names = ["contributed", "uncontributed"]
    async with db_engine.begin() as conn:
        await conn.execute(
            sa.insert(AppConfigDefinitionRow.__table__).values([
                {"config_name": config_name} for config_name in config_names
            ])
        )
        await conn.execute(
            sa.insert(AppConfigAllowListRow.__table__).values([
                {
                    "config_name": config_name,
                    "scope_type": scope_type,
                    "rank": scope_type.default_rank(),
                }
                for config_name in config_names
                for scope_type in AppConfigScopeType
            ])
        )
        await conn.execute(
            sa.insert(AppConfigFragmentRow.__table__).values([
                {
                    "id": uuid.uuid4(),
                    "config_name": "contributed",
                    "scope_type": AppConfigScopeType.PUBLIC,
                    "scope_id": None,
                    "config": {"mode": "light", "lang": "en"},
                },
                {
                    "id": uuid.uuid4(),
                    "config_name": "contributed",
                    "scope_type": AppConfigScopeType.USER,
                    "scope_id": regular_user_fixture.user_uuid,
                    "config": {"mode": "dark"},
                },
            ])
        )
    yield
    # The definition cascades to its allow-list entries and their fragments.
    async with db_engine.begin() as conn:
        await conn.execute(
            AppConfigDefinitionRow.__table__.delete().where(
                AppConfigDefinitionRow.__table__.c.config_name.in_(config_names)
            )
        )
