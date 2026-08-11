from __future__ import annotations

from collections.abc import AsyncIterator, Awaitable, Callable, Mapping
from typing import TYPE_CHECKING, Any
from unittest.mock import MagicMock

import pytest
import sqlalchemy as sa
import yarl

from ai.backend.client.v2.auth import HMACAuth, NoAuth
from ai.backend.client.v2.config import ClientConfig
from ai.backend.client.v2.v2_registry import V2ClientRegistry
from ai.backend.common.data.app_config.types import AppConfigScopeType
from ai.backend.common.identifier.app_config import AppConfigScopeID
from ai.backend.manager.actions.monitors import ActionMonitors
from ai.backend.manager.actions.registry import ProcessorDependencies, ProcessorRegistry
from ai.backend.manager.actions.v2.validators import ActionValidators
from ai.backend.manager.api.adapters.app_config.adapter import AppConfigAdapter
from ai.backend.manager.api.adapters.app_config_allow_list.adapter import AppConfigAllowListAdapter
from ai.backend.manager.api.adapters.app_config_definition.adapter import (
    AppConfigDefinitionAdapter,
)
from ai.backend.manager.api.rest.routing import RouteRegistry
from ai.backend.manager.api.rest.types import RouteDeps
from ai.backend.manager.api.rest.v2.app_config.handler import V2AppConfigHandler
from ai.backend.manager.api.rest.v2.app_config.registry import register_v2_app_config_routes
from ai.backend.manager.api.rest.v2.app_config_allow_list.handler import (
    V2AppConfigAllowListHandler,
)
from ai.backend.manager.api.rest.v2.app_config_allow_list.registry import (
    register_v2_app_config_allow_list_routes,
)
from ai.backend.manager.api.rest.v2.app_config_definition.handler import (
    V2AppConfigDefinitionHandler,
)
from ai.backend.manager.api.rest.v2.app_config_definition.registry import (
    register_v2_app_config_definition_routes,
)
from ai.backend.manager.models.app_config_allow_list.row import AppConfigAllowListRow
from ai.backend.manager.models.app_config_definition.row import AppConfigDefinitionRow
from ai.backend.manager.models.app_config_fragment.row import AppConfigFragmentRow
from ai.backend.manager.models.utils import ExtendedAsyncSAEngine
from ai.backend.manager.repositories.app_config_definition.repository import (
    AppConfigDefinitionRepository,
)
from ai.backend.manager.repositories.app_config_fragment.repository import (
    AppConfigFragmentRepository,
)
from ai.backend.manager.repositories.ops.rbac.provider import RBACOpsProvider
from ai.backend.manager.repositories.ops.repository import OpsRepository
from ai.backend.manager.repositories.ops.v2.provider import V2DBOpsProvider
from ai.backend.manager.services.app_config.processors import AppConfigProcessors
from ai.backend.manager.services.app_config.service import AppConfigService
from ai.backend.manager.services.app_config_allow_list.processors import (
    AppConfigAllowListProcessors,
)
from ai.backend.manager.services.app_config_definition.processors import (
    AppConfigDefinitionProcessors,
)
from ai.backend.manager.services.app_config_definition.service import AppConfigDefinitionService

if TYPE_CHECKING:
    from tests.component.conftest import ServerInfo, UserFixtureData

    from ai.backend.testutils.fixtures import DomainFixtureData


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
def app_config_definition_adapter(
    database_engine: ExtendedAsyncSAEngine,
) -> AppConfigDefinitionAdapter:
    repository = AppConfigDefinitionRepository(RBACOpsProvider(database_engine))
    processors = MagicMock()
    processors.app_config_definition = AppConfigDefinitionProcessors(
        AppConfigDefinitionService(repository), []
    )
    return AppConfigDefinitionAdapter(processors)


@pytest.fixture()
def app_config_allow_list_adapter(
    database_engine: ExtendedAsyncSAEngine,
) -> AppConfigAllowListAdapter:
    """This domain runs straight against ops, so it takes a processor group, not a service."""
    processors = MagicMock()
    processors.app_config_allow_list = AppConfigAllowListProcessors(
        ProcessorRegistry(
            ProcessorDependencies(
                monitors=ActionMonitors(),
                validators=ActionValidators(),
                repository=OpsRepository(V2DBOpsProvider(database_engine)),
            )
        ).group()
    )
    return AppConfigAllowListAdapter(processors)


@pytest.fixture()
def server_module_registries(
    route_deps: RouteDeps,
    app_config_adapter: AppConfigAdapter,
    app_config_definition_adapter: AppConfigDefinitionAdapter,
    app_config_allow_list_adapter: AppConfigAllowListAdapter,
) -> list[RouteRegistry]:
    v2_registry = RouteRegistry.create("v2", route_deps.cors_options)
    v2_registry.add_subregistry(
        register_v2_app_config_routes(V2AppConfigHandler(adapter=app_config_adapter), route_deps)
    )
    v2_registry.add_subregistry(
        register_v2_app_config_definition_routes(
            V2AppConfigDefinitionHandler(adapter=app_config_definition_adapter), route_deps
        )
    )
    v2_registry.add_subregistry(
        register_v2_app_config_allow_list_routes(
            V2AppConfigAllowListHandler(adapter=app_config_allow_list_adapter), route_deps
        )
    )
    return [v2_registry]


type SeedFragments = Callable[
    [str, Mapping[AppConfigScopeType, dict[str, Any] | None]], Awaitable[None]
]


@pytest.fixture()
async def seed_colliding_fragments(
    database_engine: ExtendedAsyncSAEngine,
    regular_user_fixture: UserFixtureData,
    domain_fixture: DomainFixtureData,
) -> AsyncIterator[SeedFragments]:
    """Registers ``config_name`` at every scope and writes the fragments the caller supplies.

    ``None`` for a scope writes no fragment there at all, which is not the same as writing one
    whose value for a key is ``null``.
    """
    seeded: list[str] = []
    scope_ids: dict[AppConfigScopeType, AppConfigScopeID | None] = {
        AppConfigScopeType.PUBLIC: None,
        AppConfigScopeType.DOMAIN: AppConfigScopeID(domain_fixture.domain_id),
        AppConfigScopeType.USER: AppConfigScopeID(regular_user_fixture.user_uuid),
    }

    async def seed(
        config_name: str, configs: Mapping[AppConfigScopeType, dict[str, Any] | None]
    ) -> None:
        seeded.append(config_name)
        async with database_engine.begin_session() as sess:
            sess.add(AppConfigDefinitionRow(config_name=config_name))
            await sess.flush()
            sess.add_all([
                AppConfigAllowListRow(
                    config_name=config_name,
                    scope_type=scope_type,
                    rank=scope_type.default_rank(),
                )
                for scope_type in AppConfigScopeType
            ])
            await sess.flush()
            sess.add_all([
                AppConfigFragmentRow(
                    config_name=config_name,
                    scope_type=scope_type,
                    scope_id=scope_ids[scope_type],
                    config=config,
                )
                for scope_type, config in configs.items()
                if config is not None
            ])

    yield seed
    async with database_engine.begin_session() as sess:
        await sess.execute(
            sa.delete(AppConfigDefinitionRow).where(AppConfigDefinitionRow.config_name.in_(seeded))
        )


@pytest.fixture()
async def user_v2_registry(
    server: ServerInfo,
    regular_user_fixture: UserFixtureData,
) -> AsyncIterator[V2ClientRegistry]:
    registry = await V2ClientRegistry.create(
        ClientConfig(endpoint=yarl.URL(server.url)),
        HMACAuth(
            access_key=regular_user_fixture.keypair.access_key,
            secret_key=regular_user_fixture.keypair.secret_key,
        ),
    )
    try:
        yield registry
    finally:
        await registry.close()


@pytest.fixture()
async def anonymous_v2_registry(server: ServerInfo) -> AsyncIterator[V2ClientRegistry]:
    """A caller that holds no credentials at all — the pre-login client."""
    registry = await V2ClientRegistry.create(ClientConfig(endpoint=yarl.URL(server.url)), NoAuth())
    try:
        yield registry
    finally:
        await registry.close()


@pytest.fixture()
async def admin_v2_registry(
    server: ServerInfo,
    admin_user_fixture: UserFixtureData,
) -> AsyncIterator[V2ClientRegistry]:
    """A superadmin caller — the only one the definition and allow-list routes admit."""
    registry = await V2ClientRegistry.create(
        ClientConfig(endpoint=yarl.URL(server.url)),
        HMACAuth(
            access_key=admin_user_fixture.keypair.access_key,
            secret_key=admin_user_fixture.keypair.secret_key,
        ),
    )
    try:
        yield registry
    finally:
        await registry.close()


@pytest.fixture()
async def registered_config_name(
    database_engine: ExtendedAsyncSAEngine,
) -> AsyncIterator[str]:
    """A config name the tests register through the API, removed here however they end.

    Purging the definition cascades to its allow-list entries, so this one delete covers
    whatever a test left behind.
    """
    config_name = "component-managed"
    yield config_name
    async with database_engine.begin_session() as sess:
        await sess.execute(
            sa.delete(AppConfigDefinitionRow).where(
                AppConfigDefinitionRow.config_name == config_name
            )
        )
