from __future__ import annotations

import pytest

from ai.backend.common.etcd import AsyncEtcd
from ai.backend.manager.api.rest.etcd.handler import EtcdHandler
from ai.backend.manager.api.rest.etcd.registry import register_etcd_routes
from ai.backend.manager.api.rest.routing import RouteRegistry
from ai.backend.manager.api.rest.types import RouteDeps
from ai.backend.manager.config.provider import ManagerConfigProvider
from ai.backend.manager.dependencies.infrastructure.redis import ValkeyClients
from ai.backend.manager.models.utils import ExtendedAsyncSAEngine
from ai.backend.manager.repositories.container_registry.repository import (
    ContainerRegistryRepository,
)
from ai.backend.manager.repositories.etcd_config.repository import EtcdConfigRepository
from ai.backend.manager.services.container_registry.processors import ContainerRegistryProcessors
from ai.backend.manager.services.container_registry.service import ContainerRegistryService
from ai.backend.manager.services.etcd_config.processors import EtcdConfigProcessors
from ai.backend.manager.services.etcd_config.service import EtcdConfigService


@pytest.fixture()
def container_registry_processors(
    database_engine: ExtendedAsyncSAEngine,
) -> ContainerRegistryProcessors:
    repo = ContainerRegistryRepository(database_engine)
    service = ContainerRegistryService(database_engine, repo)
    return ContainerRegistryProcessors(service=service, action_monitors=[])


@pytest.fixture()
def etcd_config_processors(
    database_engine: ExtendedAsyncSAEngine,
    config_provider: ManagerConfigProvider,
    async_etcd: AsyncEtcd,
    valkey_clients: ValkeyClients,
) -> EtcdConfigProcessors:
    repo = EtcdConfigRepository(database_engine)
    service = EtcdConfigService(
        repository=repo,
        config_provider=config_provider,
        etcd=async_etcd,
        valkey_stat=valkey_clients.stat,
    )
    return EtcdConfigProcessors(service=service, action_monitors=[])


@pytest.fixture()
def server_module_registries(
    route_deps: RouteDeps,
    container_registry_processors: ContainerRegistryProcessors,
    etcd_config_processors: EtcdConfigProcessors,
    config_provider: ManagerConfigProvider,
) -> list[RouteRegistry]:
    """Load only the modules required for etcd_config component tests."""
    return [
        register_etcd_routes(
            EtcdHandler(
                container_registry=container_registry_processors,
                etcd_config=etcd_config_processors,
            ),
            route_deps,
            pidx=0,
            config_provider=config_provider,
        ),
    ]
