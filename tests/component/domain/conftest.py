from __future__ import annotations

import secrets
from collections.abc import AsyncIterator, Callable, Coroutine
from contextlib import asynccontextmanager
from typing import Any
from unittest.mock import MagicMock

import pytest
import sqlalchemy as sa
from sqlalchemy.ext.asyncio.engine import AsyncEngine as SAEngine

from ai.backend.client.v2.registry import BackendAIClientRegistry
from ai.backend.common.dto.manager.domain import (
    CreateDomainRequest,
    CreateDomainResponse,
    PurgeDomainRequest,
)

# Statically imported so that Pants includes these modules in the test PEX.
# build_root_app() loads them at runtime via importlib.import_module(),
# which Pants cannot trace statically.
from ai.backend.manager.api import auth as _auth_api
from ai.backend.manager.api import domain as _domain_api
from ai.backend.manager.api.context import RootContext
from ai.backend.manager.api.types import CleanupContext
from ai.backend.manager.models.domain import domains
from ai.backend.manager.models.resource_policy.row import ProjectResourcePolicyRow
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

_DOMAIN_SERVER_SUBAPP_MODULES = (_auth_api, _domain_api)

DomainFactory = Callable[..., Coroutine[Any, Any, CreateDomainResponse]]


@asynccontextmanager
async def _domain_domain_ctx(root_ctx: RootContext) -> AsyncIterator[None]:
    """Set up repositories and processors for domain-domain component tests.

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
    """Load only the subapps required for domain-domain tests."""
    return [".auth", ".domain"]


@pytest.fixture()
def server_cleanup_contexts() -> list[CleanupContext]:
    """Provide cleanup contexts for domain-domain component tests.

    Uses production contexts from server.py for real infrastructure:
    - redis_ctx: all 8 Valkey clients
    - database_ctx: real database connection
    - monitoring_ctx: real (empty-plugin) error and stats monitors
    - storage_manager_ctx: real StorageSessionManager (empty proxy config)
    - message_queue_ctx: real Redis-backed message queue
    - event_producer_ctx: real EventProducer + EventFetcher
    - event_hub_ctx: real EventHub
    - background_task_ctx: real BackgroundTaskManager
    - _domain_domain_ctx: repositories and processors wired with real clients
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
        _domain_domain_ctx,
    ]


@pytest.fixture()
async def project_resource_policy_fixture(
    db_engine: SAEngine,
) -> AsyncIterator[None]:
    """Insert the 'default' project_resource_policy required for domain group creation.

    When a domain is created, the API internally creates a default group that
    references resource_policy="default" in project_resource_policies.  This
    fixture seeds that row so the FK constraint is satisfied.
    Uses on_conflict_do_nothing() for idempotency in case the row already exists.
    """
    async with db_engine.begin() as conn:
        await conn.execute(
            sa.insert(ProjectResourcePolicyRow.__table__)
            .values(
                name="default",
                max_vfolder_count=0,
                max_quota_scope_size=-1,
                max_network_count=3,
            )
            .on_conflict_do_nothing()
        )
    yield
    async with db_engine.begin() as conn:
        await conn.execute(
            ProjectResourcePolicyRow.__table__.delete().where(
                ProjectResourcePolicyRow.__table__.c.name == "default"
            )
        )


@pytest.fixture()
async def domain_factory(
    admin_registry: BackendAIClientRegistry,
    db_engine: SAEngine,
    project_resource_policy_fixture: None,
) -> AsyncIterator[DomainFactory]:
    """Factory fixture that creates domains via SDK and purges them on teardown."""
    created_names: list[str] = []

    async def _create(**overrides: Any) -> CreateDomainResponse:
        unique = secrets.token_hex(4)
        params: dict[str, Any] = {
            "name": f"test-domain-{unique}",
            "description": f"Test domain {unique}",
            "is_active": True,
        }
        params.update(overrides)
        result = await admin_registry.domain.create(CreateDomainRequest(**params))
        created_names.append(result.domain.name)
        return result

    yield _create

    for name in reversed(created_names):
        try:
            await admin_registry.domain.purge(PurgeDomainRequest(name=name))
        except Exception:
            # Fallback: remove domain rows directly when the API purge cannot complete.
            async with db_engine.begin() as conn:
                await conn.execute(domains.delete().where(domains.c.name == name))


@pytest.fixture()
async def target_domain(
    domain_factory: DomainFactory,
) -> CreateDomainResponse:
    """Pre-created domain for tests that need an existing domain."""
    return await domain_factory()
