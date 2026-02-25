from __future__ import annotations

import secrets
import uuid
from collections.abc import AsyncIterator, Callable, Coroutine
from contextlib import asynccontextmanager
from typing import Any
from unittest.mock import AsyncMock, MagicMock

import pytest
import sqlalchemy as sa
from sqlalchemy.ext.asyncio.engine import AsyncEngine as SAEngine

from ai.backend.manager.api import ManagerStatus
from ai.backend.manager.api import auth as _auth_api
from ai.backend.manager.api import object_storage as _object_storage_api
from ai.backend.manager.api.context import RootContext
from ai.backend.manager.api.types import CleanupContext
from ai.backend.manager.models.object_storage import ObjectStorageRow
from ai.backend.manager.models.storage_namespace.row import StorageNamespaceRow
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

# Statically imported so that Pants includes these modules in the test PEX.
# build_root_app() loads them at runtime via importlib.import_module(),
# which Pants cannot trace statically.
_OBJECT_STORAGE_SERVER_SUBAPP_MODULES = (_auth_api, _object_storage_api)

ObjectStorageFixtureData = dict[str, Any]
ObjectStorageFactory = Callable[..., Coroutine[Any, Any, ObjectStorageFixtureData]]
StorageNamespaceFixtureData = dict[str, Any]
StorageNamespaceFactory = Callable[..., Coroutine[Any, Any, StorageNamespaceFixtureData]]


@asynccontextmanager
async def _object_storage_domain_ctx(root_ctx: RootContext) -> AsyncIterator[None]:
    """Set up repositories and processors for object-storage-domain component tests."""
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


@pytest.fixture()
def server_subapp_pkgs() -> list[str]:
    """Load only the subapps required for object-storage-domain tests."""
    return [".auth", ".object_storage"]


@pytest.fixture()
def server_cleanup_contexts() -> list[CleanupContext]:
    """Provide cleanup contexts for object-storage-domain component tests."""
    return [
        redis_ctx,
        database_ctx,
        monitoring_ctx,
        storage_manager_ctx,
        message_queue_ctx,
        event_producer_ctx,
        event_hub_ctx,
        background_task_ctx,
        _object_storage_domain_ctx,
    ]


@pytest.fixture()
async def object_storage_factory(
    db_engine: SAEngine,
) -> AsyncIterator[ObjectStorageFactory]:
    """Factory that inserts ObjectStorageRow directly into DB.

    Yields a factory callable and cleans up all created rows on teardown.
    """
    created_ids: list[uuid.UUID] = []

    async def _create(**overrides: Any) -> ObjectStorageFixtureData:
        unique = secrets.token_hex(4)
        storage_id = uuid.uuid4()
        defaults: dict[str, Any] = {
            "id": storage_id,
            "name": f"test-storage-{unique}",
            "host": "s3.example.com",
            "access_key": f"AK-{unique}",
            "secret_key": f"SK-{unique}",
            "endpoint": f"https://s3.example.com/{unique}",
            "region": "us-east-1",
        }
        defaults.update(overrides)
        async with db_engine.begin() as conn:
            await conn.execute(sa.insert(ObjectStorageRow.__table__).values(**defaults))
        created_ids.append(defaults["id"])
        return defaults

    yield _create

    async with db_engine.begin() as conn:
        for sid in reversed(created_ids):
            await conn.execute(
                sa.delete(StorageNamespaceRow.__table__).where(
                    StorageNamespaceRow.__table__.c.storage_id == sid
                )
            )
            await conn.execute(
                sa.delete(ObjectStorageRow.__table__).where(ObjectStorageRow.__table__.c.id == sid)
            )


@pytest.fixture()
async def storage_namespace_factory(
    db_engine: SAEngine,
) -> AsyncIterator[StorageNamespaceFactory]:
    """Factory that inserts StorageNamespaceRow directly into DB.

    Yields a factory callable and cleans up all created rows on teardown.
    """
    created_ids: list[uuid.UUID] = []

    async def _create(**overrides: Any) -> StorageNamespaceFixtureData:
        unique = secrets.token_hex(4)
        ns_id = uuid.uuid4()
        defaults: dict[str, Any] = {
            "id": ns_id,
            "namespace": f"test-bucket-{unique}",
        }
        defaults.update(overrides)
        if "storage_id" not in defaults:
            raise ValueError("storage_id is required for storage_namespace_factory")
        async with db_engine.begin() as conn:
            await conn.execute(sa.insert(StorageNamespaceRow.__table__).values(**defaults))
        created_ids.append(defaults["id"])
        return defaults

    yield _create

    async with db_engine.begin() as conn:
        for nid in reversed(created_ids):
            await conn.execute(
                sa.delete(StorageNamespaceRow.__table__).where(
                    StorageNamespaceRow.__table__.c.id == nid
                )
            )
