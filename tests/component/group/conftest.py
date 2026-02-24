from __future__ import annotations

import secrets
import uuid
from collections.abc import AsyncIterator, Callable, Coroutine
from contextlib import asynccontextmanager
from typing import Any
from unittest.mock import MagicMock

import pytest
from sqlalchemy.dialects.postgresql import insert as pg_insert
from sqlalchemy.ext.asyncio.engine import AsyncEngine as SAEngine

from ai.backend.client.v2.registry import BackendAIClientRegistry
from ai.backend.common.dto.manager.domain import (
    CreateDomainRequest,
    CreateDomainResponse,
    PurgeDomainRequest,
)
from ai.backend.common.dto.manager.group import (
    CreateGroupRequest,
    CreateGroupResponse,
)

# Statically imported so that Pants includes these modules in the test PEX.
# build_root_app() loads them at runtime via importlib.import_module(),
# which Pants cannot trace statically.
from ai.backend.manager.api import auth as _auth_api
from ai.backend.manager.api import groups as _groups_api
from ai.backend.manager.api.context import RootContext
from ai.backend.manager.api.types import CleanupContext
from ai.backend.manager.models.domain import domains
from ai.backend.manager.models.group import association_groups_users, groups
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

_GROUP_SERVER_SUBAPP_MODULES = (_auth_api, _groups_api)

DomainFactory = Callable[..., Coroutine[Any, Any, CreateDomainResponse]]
GroupFactory = Callable[..., Coroutine[Any, Any, CreateGroupResponse]]


@asynccontextmanager
async def _group_domain_ctx(root_ctx: RootContext) -> AsyncIterator[None]:
    """Set up repositories and processors for group component tests.

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
    """Load only the subapps required for group component tests."""
    return [".auth", ".groups"]


@pytest.fixture()
def server_cleanup_contexts() -> list[CleanupContext]:
    """Provide cleanup contexts for group component tests."""
    return [
        redis_ctx,
        database_ctx,
        monitoring_ctx,
        storage_manager_ctx,
        message_queue_ctx,
        event_producer_ctx,
        event_hub_ctx,
        background_task_ctx,
        _group_domain_ctx,
    ]


@pytest.fixture()
async def project_resource_policy_fixture(
    db_engine: SAEngine,
) -> AsyncIterator[None]:
    """Insert the 'default' project_resource_policy required for group creation.

    When a domain is created, the API internally creates a default group that
    references resource_policy="default" in project_resource_policies.  This
    fixture seeds that row so the FK constraint is satisfied.
    Uses on_conflict_do_nothing() for idempotency in case the row already exists.
    """
    async with db_engine.begin() as conn:
        await conn.execute(
            pg_insert(ProjectResourcePolicyRow.__table__)
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
async def domain_for_group_fixture(
    admin_registry: BackendAIClientRegistry,
    db_engine: SAEngine,
    project_resource_policy_fixture: None,
) -> AsyncIterator[str]:
    """Create a domain via SDK for group creation tests, purge on teardown."""
    unique = secrets.token_hex(4)
    domain_name = f"test-grp-domain-{unique}"
    await admin_registry.domain.create(
        CreateDomainRequest(
            name=domain_name,
            description=f"Test domain for groups {unique}",
            is_active=True,
        )
    )
    yield domain_name

    try:
        # Delete all groups in the domain first
        async with db_engine.begin() as conn:
            await conn.execute(groups.delete().where(groups.c.domain_name == domain_name))
        await admin_registry.domain.purge(PurgeDomainRequest(name=domain_name))
    except Exception:
        async with db_engine.begin() as conn:
            await conn.execute(groups.delete().where(groups.c.domain_name == domain_name))
            await conn.execute(domains.delete().where(domains.c.name == domain_name))


@pytest.fixture()
async def group_factory(
    admin_registry: BackendAIClientRegistry,
    db_engine: SAEngine,
    domain_for_group_fixture: str,
) -> AsyncIterator[GroupFactory]:
    """Factory fixture that creates groups via SDK and deletes them on teardown."""
    created_ids: list[uuid.UUID] = []

    async def _create(**overrides: Any) -> CreateGroupResponse:
        unique = secrets.token_hex(4)
        params: dict[str, Any] = {
            "name": f"test-group-{unique}",
            "domain_name": domain_for_group_fixture,
            "description": f"Test group {unique}",
        }
        params.update(overrides)
        result = await admin_registry.group.create(CreateGroupRequest(**params))
        created_ids.append(result.group.id)
        return result

    yield _create

    for gid in reversed(created_ids):
        try:
            await admin_registry.group.delete(gid)
        except Exception:
            # Fallback: remove group rows directly when the API delete cannot complete.
            async with db_engine.begin() as conn:
                await conn.execute(
                    association_groups_users.delete().where(
                        association_groups_users.c.group_id == gid
                    )
                )
                await conn.execute(groups.delete().where(groups.c.id == gid))


@pytest.fixture()
async def target_group(
    group_factory: GroupFactory,
) -> CreateGroupResponse:
    """Pre-created group for tests that need an existing group."""
    return await group_factory()
