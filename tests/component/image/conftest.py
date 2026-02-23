from __future__ import annotations

import uuid
from collections.abc import AsyncIterator, Callable
from contextlib import asynccontextmanager
from unittest.mock import AsyncMock, MagicMock

import pytest
import sqlalchemy as sa
from sqlalchemy.ext.asyncio.engine import AsyncEngine as SAEngine

from ai.backend.common.container_registry import ContainerRegistryType
from ai.backend.manager.api import ManagerStatus

# Statically imported so that Pants includes these modules in the test PEX.
# build_root_app() loads them at runtime via importlib.import_module(),
# which Pants cannot trace statically.
from ai.backend.manager.api import auth as _auth_api
from ai.backend.manager.api import image as _image_api
from ai.backend.manager.api.context import RootContext
from ai.backend.manager.api.types import CleanupContext
from ai.backend.manager.data.image.types import ImageStatus, ImageType
from ai.backend.manager.models.container_registry import ContainerRegistryRow
from ai.backend.manager.models.image.row import ImageAliasRow, ImageRow
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

_IMAGE_SERVER_SUBAPP_MODULES = (_auth_api, _image_api)


@asynccontextmanager
async def _image_domain_ctx(root_ctx: RootContext) -> AsyncIterator[None]:
    """Set up repositories and processors for image-domain component tests.

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
    """Load only the subapps required for image-domain tests."""
    return [".auth", ".image"]


@pytest.fixture()
def server_cleanup_contexts() -> list[CleanupContext]:
    """Provide cleanup contexts for image-domain component tests."""
    return [
        redis_ctx,
        database_ctx,
        monitoring_ctx,
        storage_manager_ctx,
        message_queue_ctx,
        event_producer_ctx,
        event_hub_ctx,
        background_task_ctx,
        _image_domain_ctx,
    ]


@pytest.fixture()
async def container_registry_fixture(
    db_engine: SAEngine,
) -> AsyncIterator[uuid.UUID]:
    """Insert a test Docker container registry and yield its UUID.

    Images require a FK to ContainerRegistryRow, so this must be created first.
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
def image_factory(
    db_engine: SAEngine,
    container_registry_fixture: uuid.UUID,
) -> Callable[..., ImageFactoryHelper]:
    """Factory that creates ImageRow entries in the DB.

    Returns a callable factory helper. Each call inserts a new image.
    Created images are tracked and cleaned up after the test.
    """
    return lambda: ImageFactoryHelper(db_engine, container_registry_fixture)


class ImageFactoryHelper:
    """Helper to create and track test ImageRow entries."""

    def __init__(self, db_engine: SAEngine, registry_id: uuid.UUID) -> None:
        self._db_engine = db_engine
        self._registry_id = registry_id
        self._created_ids: list[uuid.UUID] = []

    async def create(
        self,
        *,
        name_suffix: str | None = None,
        architecture: str = "x86_64",
        image_type: ImageType = ImageType.COMPUTE,
        status: ImageStatus = ImageStatus.ALIVE,
    ) -> uuid.UUID:
        """Insert an ImageRow and return its UUID."""
        image_id = uuid.uuid4()
        suffix = name_suffix or image_id.hex[:8]
        image_name = f"test-image-{suffix}"
        canonical = f"registry.test.local/testproject/{image_name}:latest"
        async with self._db_engine.begin() as conn:
            await conn.execute(
                sa.insert(ImageRow.__table__).values(
                    id=image_id,
                    name=canonical,
                    project="testproject",
                    image=image_name,
                    tag="latest",
                    registry="registry.test.local",
                    registry_id=self._registry_id,
                    architecture=architecture,
                    config_digest=f"sha256:{image_id.hex * 2}",
                    size_bytes=1024000,
                    is_local=False,
                    type=image_type,
                    accelerators=None,
                    labels={},
                    resources={
                        "cpu": {"min": "1", "max": "4"},
                        "mem": {"min": "256m", "max": "4g"},
                    },
                    status=status,
                )
            )
        self._created_ids.append(image_id)
        return image_id

    async def cleanup(self) -> None:
        """Remove all images created by this factory.

        Deletes ImageAliasRow entries first to avoid FK violations,
        since image_aliases.image references images.id.
        """
        if not self._created_ids:
            return
        async with self._db_engine.begin() as conn:
            await conn.execute(
                ImageAliasRow.__table__.delete().where(
                    ImageAliasRow.__table__.c.image.in_(self._created_ids)
                )
            )
            await conn.execute(
                ImageRow.__table__.delete().where(ImageRow.__table__.c.id.in_(self._created_ids))
            )


@pytest.fixture()
async def image_fixture(
    image_factory: Callable[..., ImageFactoryHelper],
) -> AsyncIterator[tuple[uuid.UUID, ImageFactoryHelper]]:
    """Create a single test image and yield (image_id, factory_helper).

    The factory helper can create additional images if needed.
    Cleans up all factory-created images after the test.
    """
    helper = image_factory()
    image_id = await helper.create()
    yield image_id, helper
    await helper.cleanup()
