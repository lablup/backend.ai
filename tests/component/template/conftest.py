from __future__ import annotations

import uuid
from collections.abc import AsyncIterator
from contextlib import asynccontextmanager
from unittest.mock import AsyncMock, MagicMock

import pytest
import sqlalchemy as sa
from sqlalchemy.ext.asyncio.engine import AsyncEngine as SAEngine

from ai.backend.manager.api import ManagerStatus
from ai.backend.manager.api.context import CleanupContext, RootContext
from ai.backend.manager.api.rest.auth.registry import register_auth_routes
from ai.backend.manager.api.rest.template.registry import register_template_routes
from ai.backend.manager.api.rest.types import ModuleRegistrar
from ai.backend.manager.models.group import GroupRow
from ai.backend.manager.models.session_template import session_templates
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


@asynccontextmanager
async def _template_domain_ctx(root_ctx: RootContext) -> AsyncIterator[None]:
    _mock_loader = MagicMock()
    _mock_loader.get_manager_status = AsyncMock(return_value=ManagerStatus.RUNNING)
    root_ctx.config_provider._legacy_etcd_config_loader = _mock_loader
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
    async with root_ctx.db.begin() as conn:
        await conn.execute(sa.delete(session_templates))


@pytest.fixture()
def server_module_registrars() -> list[ModuleRegistrar]:
    """Load only the modules required for template-domain tests."""
    return [register_auth_routes, register_template_routes]


@pytest.fixture()
def server_cleanup_contexts() -> list[CleanupContext]:
    """Provide cleanup contexts for template-domain component tests."""
    return [
        redis_ctx,
        database_ctx,
        monitoring_ctx,
        storage_manager_ctx,
        message_queue_ctx,
        event_producer_ctx,
        event_hub_ctx,
        background_task_ctx,
        _template_domain_ctx,
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
