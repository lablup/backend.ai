from __future__ import annotations

import uuid
from collections.abc import AsyncIterator
from contextlib import asynccontextmanager
from unittest.mock import MagicMock

import pytest
import sqlalchemy as sa
from sqlalchemy.ext.asyncio.engine import AsyncEngine as SAEngine

from ai.backend.common.container_registry import ContainerRegistryType

# Statically imported so that Pants includes these modules in the test PEX.
# build_root_app() loads them at runtime via importlib.import_module(),
# which Pants cannot trace statically.
from ai.backend.manager.api import auth as _auth_api
from ai.backend.manager.api import container_registry as _container_registry_api
from ai.backend.manager.api.context import RootContext
from ai.backend.manager.api.types import CleanupContext
from ai.backend.manager.models.container_registry import ContainerRegistryRow
from ai.backend.manager.repositories.repositories import Repositories
from ai.backend.manager.repositories.types import RepositoryArgs
from ai.backend.manager.server import (
    background_task_ctx,
    database_ctx,
    event_hub_ctx,
    event_producer_ctx,
    message_queue_ctx,
    monitoring_ctx,
    redis_ctx,
    storage_manager_ctx,
)
from ai.backend.manager.services.processors import ProcessorArgs, Processors, ServiceArgs

_CONTAINER_REGISTRY_SERVER_SUBAPP_MODULES = (_auth_api, _container_registry_api)


@asynccontextmanager
async def _container_registry_domain_ctx(root_ctx: RootContext) -> AsyncIterator[None]:
    """Set up repositories and processors for container-registry-domain component tests.

    Relies on the preceding cleanup contexts having already initialized:
    - redis_ctx      → root_ctx.valkey_* (all 8 clients)
    - database_ctx   → root_ctx.db
    - monitoring_ctx → root_ctx.error_monitor / stats_monitor
    - storage_manager_ctx  → root_ctx.storage_manager
    - message_queue_ctx    → root_ctx.message_queue
    - event_producer_ctx   → root_ctx.event_producer / event_fetcher
    - event_hub_ctx        → root_ctx.event_hub
    - background_task_ctx  → root_ctx.background_task_manager

    Only agent_registry is left as MagicMock because it requires live gRPC
    connections to real agents, which are not available in component tests.
    """
    root_ctx.repositories = Repositories.create(
        RepositoryArgs(
            db=root_ctx.db,
            storage_manager=root_ctx.storage_manager,
            config_provider=root_ctx.config_provider,
            valkey_stat_client=root_ctx.valkey_stat,
            valkey_schedule_client=root_ctx.valkey_schedule,
            valkey_image_client=root_ctx.valkey_image,
            valkey_live_client=root_ctx.valkey_live,
        )
    )
    root_ctx.processors = Processors.create(
        ProcessorArgs(
            service_args=ServiceArgs(
                db=root_ctx.db,
                repositories=root_ctx.repositories,
                etcd=root_ctx.etcd,
                config_provider=root_ctx.config_provider,
                storage_manager=root_ctx.storage_manager,
                valkey_stat_client=root_ctx.valkey_stat,
                valkey_live=root_ctx.valkey_live,
                valkey_artifact_client=root_ctx.valkey_artifact,
                error_monitor=root_ctx.error_monitor,
                event_fetcher=root_ctx.event_fetcher,
                background_task_manager=root_ctx.background_task_manager,
                event_hub=root_ctx.event_hub,
                event_producer=root_ctx.event_producer,
                # agent_registry requires gRPC connections to real agents — not feasible
                # in the component test environment; kept as MagicMock.
                agent_registry=MagicMock(),
                idle_checker_host=MagicMock(),
                event_dispatcher=MagicMock(),
                hook_plugin_ctx=MagicMock(),
                scheduling_controller=MagicMock(),
                deployment_controller=MagicMock(),
                revision_generator_registry=MagicMock(),
                agent_cache=MagicMock(),
                notification_center=MagicMock(),
                appproxy_client_pool=MagicMock(),
                prometheus_client=MagicMock(),
            ),
        ),
        [],
    )
    yield


@pytest.fixture()
def server_subapp_pkgs() -> list[str]:
    """Load only the subapps required for container-registry-domain tests."""
    return [".auth", ".container_registry"]


@pytest.fixture()
def server_cleanup_contexts() -> list[CleanupContext]:
    """Provide cleanup contexts for container-registry-domain component tests.

    Uses production contexts from server.py for real infrastructure:
    - redis_ctx: all 8 Valkey clients
    - database_ctx: real database connection
    - monitoring_ctx: real (empty-plugin) error and stats monitors
    - storage_manager_ctx: real StorageSessionManager (empty proxy config)
    - message_queue_ctx: real Redis-backed message queue
    - event_producer_ctx: real EventProducer + EventFetcher
    - event_hub_ctx: real EventHub
    - background_task_ctx: real BackgroundTaskManager
    - _container_registry_domain_ctx: repositories and processors wired with real clients
    """
    return [
        redis_ctx,
        database_ctx,
        monitoring_ctx,
        storage_manager_ctx,
        message_queue_ctx,
        event_producer_ctx,
        event_hub_ctx,
        background_task_ctx,
        _container_registry_domain_ctx,
    ]


@pytest.fixture()
async def container_registry_fixture(
    db_engine: SAEngine,
) -> AsyncIterator[uuid.UUID]:
    """Insert a test Docker container registry and yield its UUID.

    Used for patch endpoint tests. Cleaned up after each test.
    """
    registry_id = uuid.uuid4()
    async with db_engine.begin() as conn:
        await conn.execute(
            sa.insert(ContainerRegistryRow.__table__).values(
                id=registry_id,
                url="https://registry.test.local",
                registry_name=f"test-registry-{registry_id.hex[:8]}",
                type=ContainerRegistryType.DOCKER,
            )
        )
    yield registry_id
    async with db_engine.begin() as conn:
        await conn.execute(
            ContainerRegistryRow.__table__.delete().where(
                ContainerRegistryRow.__table__.c.id == registry_id
            )
        )


@pytest.fixture()
async def harbor_registry_fixture(
    db_engine: SAEngine,
) -> AsyncIterator[uuid.UUID]:
    """Insert a test HARBOR2 container registry and yield its UUID.

    Used for harbor webhook endpoint tests. Cleaned up after each test.
    """
    registry_id = uuid.uuid4()
    async with db_engine.begin() as conn:
        await conn.execute(
            sa.insert(ContainerRegistryRow.__table__).values(
                id=registry_id,
                url="https://harbor.test.local",
                registry_name=f"harbor-test-{registry_id.hex[:8]}",
                type=ContainerRegistryType.HARBOR2,
                project="testproject",
            )
        )
    yield registry_id
    async with db_engine.begin() as conn:
        await conn.execute(
            ContainerRegistryRow.__table__.delete().where(
                ContainerRegistryRow.__table__.c.id == registry_id
            )
        )
