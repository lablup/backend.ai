"""Component tests for resource allocation visibility settings.

Tests that hide_agents and group_resource_visibility configuration options
correctly control which breakdown sections are visible to non-admin users
in the effective allocation response.
"""

from __future__ import annotations

import uuid
from collections.abc import AsyncIterator, Callable
from typing import TYPE_CHECKING
from unittest.mock import MagicMock

import pytest
import yarl

from ai.backend.client.v2.auth import HMACAuth
from ai.backend.client.v2.config import ClientConfig
from ai.backend.client.v2.v2_registry import V2ClientRegistry
from ai.backend.common.dto.manager.v2.resource_allocation.request import (
    EffectiveResourceAllocationInput,
)
from ai.backend.common.dto.manager.v2.resource_allocation.response import (
    EffectiveResourceAllocationPayload,
)
from ai.backend.manager.actions.validators import ActionValidators
from ai.backend.manager.api.adapters.resource_allocation import ResourceAllocationAdapter
from ai.backend.manager.api.rest.routing import RouteRegistry
from ai.backend.manager.api.rest.types import RouteDeps
from ai.backend.manager.api.rest.v2.resource_allocation.handler import (
    V2ResourceAllocationHandler,
)
from ai.backend.manager.api.rest.v2.resource_allocation.registry import (
    register_v2_resource_allocation_routes,
)
from ai.backend.manager.config.provider import ManagerConfigProvider
from ai.backend.manager.config.unified import ManagerUnifiedConfig
from ai.backend.manager.dependencies.infrastructure.redis import ValkeyClients
from ai.backend.manager.models.utils import ExtendedAsyncSAEngine
from ai.backend.manager.repositories.resource_allocation.repository import (
    ResourceAllocationRepository,
)
from ai.backend.manager.repositories.resource_preset.repository import (
    ResourcePresetRepository,
)
from ai.backend.manager.services.processors import Processors
from ai.backend.manager.services.resource_allocation.processors import (
    ResourceAllocationProcessors,
)
from ai.backend.manager.services.resource_allocation.service import (
    ResourceAllocationService,
)

if TYPE_CHECKING:
    from tests.component.conftest import ServerInfo, UserFixtureData


# ---------------------------------------------------------------------------
# Config provider fixtures with visibility settings
# ---------------------------------------------------------------------------


def _make_config_provider(
    base_provider: ManagerConfigProvider,
    factory: Callable[[ManagerUnifiedConfig], ManagerConfigProvider],
    *,
    hide_agents: bool = False,
    group_resource_visibility: bool = False,
) -> ManagerConfigProvider:
    """Create a config provider with custom visibility settings.

    Copies the base config and patches the manager.hide_agents and
    api.resources.group_resource_visibility fields.
    Uses the factory fixture (config_provider_factory) from conftest to create
    a properly typed _TestConfigProvider instance.
    """
    base_config = base_provider.config
    config_dict = base_config.model_dump(mode="python")
    config_dict["manager"]["hide_agents"] = hide_agents
    if group_resource_visibility:
        if config_dict.get("api") is None:
            config_dict["api"] = {}
        if config_dict["api"].get("resources") is None:
            config_dict["api"]["resources"] = {}
        config_dict["api"]["resources"]["group_resource_visibility"] = True
    else:
        if config_dict.get("api") and config_dict["api"].get("resources"):
            config_dict["api"]["resources"]["group_resource_visibility"] = False
    new_config = ManagerUnifiedConfig.model_validate(config_dict)
    return factory(new_config)


def _build_registries(
    route_deps: RouteDeps,
    ra_processors: ResourceAllocationProcessors,
    config_provider: ManagerConfigProvider,
) -> list[RouteRegistry]:
    """Build route registries with the given config provider."""
    processors = MagicMock(spec=Processors)
    processors.resource_allocation = ra_processors
    adapter = ResourceAllocationAdapter(
        processors=processors,
        config_provider=config_provider,
    )
    handler = V2ResourceAllocationHandler(adapter=adapter)
    v2_reg = RouteRegistry.create("v2", route_deps.cors_options)
    v2_reg.add_subregistry(register_v2_resource_allocation_routes(handler, route_deps))
    return [v2_reg]


# ---------------------------------------------------------------------------
# Test: hide_agents=True hides resource_group from regular user
# ---------------------------------------------------------------------------


class TestHideAgentsVisibility:
    """When hide_agents=True, regular users should NOT see resource_group in breakdown."""

    @pytest.fixture()
    def config_provider_hide_agents(
        self,
        config_provider: ManagerConfigProvider,
        config_provider_factory: Callable[[ManagerUnifiedConfig], ManagerConfigProvider],
    ) -> ManagerConfigProvider:
        return _make_config_provider(config_provider, config_provider_factory, hide_agents=True)

    @pytest.fixture()
    def resource_allocation_processors_hide(
        self,
        database_engine: ExtendedAsyncSAEngine,
        config_provider_hide_agents: ManagerConfigProvider,
        valkey_clients: ValkeyClients,
    ) -> ResourceAllocationProcessors:
        ra_repo = ResourceAllocationRepository(
            db=database_engine,
            config_provider=config_provider_hide_agents,
        )
        rp_repo = ResourcePresetRepository(
            db=database_engine,
            valkey_stat=valkey_clients.stat,
            config_provider=config_provider_hide_agents,
        )
        service = ResourceAllocationService(
            resource_allocation_repository=ra_repo,
            resource_preset_repository=rp_repo,
        )
        return ResourceAllocationProcessors(
            service=service,
            action_monitors=[],
            validators=MagicMock(spec=ActionValidators),
        )

    @pytest.fixture()
    def server_module_registries(
        self,
        route_deps: RouteDeps,
        resource_allocation_processors_hide: ResourceAllocationProcessors,
        config_provider_hide_agents: ManagerConfigProvider,
    ) -> list[RouteRegistry]:
        return _build_registries(
            route_deps,
            resource_allocation_processors_hide,
            config_provider_hide_agents,
        )

    @pytest.fixture()
    async def user_v2_registry(
        self,
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
    async def admin_v2_registry(
        self,
        server: ServerInfo,
        admin_user_fixture: UserFixtureData,
    ) -> AsyncIterator[V2ClientRegistry]:
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

    async def test_regular_user_effective_hides_resource_group(
        self,
        user_v2_registry: V2ClientRegistry,
        group_fixture: uuid.UUID,
        scaling_group_fixture: str,
    ) -> None:
        """Regular user with hide_agents=True should get resource_group=null."""
        result = await user_v2_registry.resource_allocation.effective(
            EffectiveResourceAllocationInput(
                project_id=group_fixture,
                resource_group_name=scaling_group_fixture,
            ),
        )
        assert isinstance(result, EffectiveResourceAllocationPayload)
        # Resource group breakdown should be hidden
        assert result.breakdown.resource_group is None
        # Assignable should still be computed
        assert isinstance(result.assignable, list)

    async def test_admin_effective_sees_resource_group_despite_hide_agents(
        self,
        admin_v2_registry: V2ClientRegistry,
        group_fixture: uuid.UUID,
        scaling_group_fixture: str,
    ) -> None:
        """Admin should see resource_group even when hide_agents=True."""
        result = await admin_v2_registry.resource_allocation.effective(
            EffectiveResourceAllocationInput(
                project_id=group_fixture,
                resource_group_name=scaling_group_fixture,
            ),
        )
        assert isinstance(result, EffectiveResourceAllocationPayload)
        # Admin sees everything regardless of settings
        assert result.breakdown.resource_group is not None


# ---------------------------------------------------------------------------
# Test: group_resource_visibility=False hides project from regular user
# ---------------------------------------------------------------------------


class TestGroupResourceVisibility:
    """When group_resource_visibility=False, regular users should NOT see project in breakdown."""

    @pytest.fixture()
    def config_provider_no_grv(
        self,
        config_provider: ManagerConfigProvider,
        config_provider_factory: Callable[[ManagerUnifiedConfig], ManagerConfigProvider],
    ) -> ManagerConfigProvider:
        return _make_config_provider(
            config_provider, config_provider_factory, group_resource_visibility=False
        )

    @pytest.fixture()
    def resource_allocation_processors_no_grv(
        self,
        database_engine: ExtendedAsyncSAEngine,
        config_provider_no_grv: ManagerConfigProvider,
        valkey_clients: ValkeyClients,
    ) -> ResourceAllocationProcessors:
        ra_repo = ResourceAllocationRepository(
            db=database_engine,
            config_provider=config_provider_no_grv,
        )
        rp_repo = ResourcePresetRepository(
            db=database_engine,
            valkey_stat=valkey_clients.stat,
            config_provider=config_provider_no_grv,
        )
        service = ResourceAllocationService(
            resource_allocation_repository=ra_repo,
            resource_preset_repository=rp_repo,
        )
        return ResourceAllocationProcessors(
            service=service,
            action_monitors=[],
            validators=MagicMock(spec=ActionValidators),
        )

    @pytest.fixture()
    def server_module_registries(
        self,
        route_deps: RouteDeps,
        resource_allocation_processors_no_grv: ResourceAllocationProcessors,
        config_provider_no_grv: ManagerConfigProvider,
    ) -> list[RouteRegistry]:
        return _build_registries(
            route_deps,
            resource_allocation_processors_no_grv,
            config_provider_no_grv,
        )

    @pytest.fixture()
    async def user_v2_registry(
        self,
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
    async def admin_v2_registry(
        self,
        server: ServerInfo,
        admin_user_fixture: UserFixtureData,
    ) -> AsyncIterator[V2ClientRegistry]:
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

    async def test_regular_user_effective_hides_project(
        self,
        user_v2_registry: V2ClientRegistry,
        group_fixture: uuid.UUID,
        scaling_group_fixture: str,
    ) -> None:
        """Regular user with group_resource_visibility=False should get project=null."""
        result = await user_v2_registry.resource_allocation.effective(
            EffectiveResourceAllocationInput(
                project_id=group_fixture,
                resource_group_name=scaling_group_fixture,
            ),
        )
        assert isinstance(result, EffectiveResourceAllocationPayload)
        # Project breakdown should be hidden when group_resource_visibility=False
        assert result.breakdown.project is None
        # Assignable should still be computed
        assert isinstance(result.assignable, list)

    async def test_admin_effective_sees_project_despite_grv_off(
        self,
        admin_v2_registry: V2ClientRegistry,
        group_fixture: uuid.UUID,
        scaling_group_fixture: str,
    ) -> None:
        """Admin should see project even when group_resource_visibility=False."""
        result = await admin_v2_registry.resource_allocation.effective(
            EffectiveResourceAllocationInput(
                project_id=group_fixture,
                resource_group_name=scaling_group_fixture,
            ),
        )
        assert isinstance(result, EffectiveResourceAllocationPayload)
        # Admin sees everything regardless of settings
        assert result.breakdown.project is not None
