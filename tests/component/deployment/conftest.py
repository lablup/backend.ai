from __future__ import annotations

import secrets
import uuid
from collections.abc import AsyncIterator, Callable, Coroutine
from typing import Any
from unittest.mock import MagicMock

import pytest
import sqlalchemy as sa
from sqlalchemy.ext.asyncio.engine import AsyncEngine as SAEngine

from ai.backend.common.container_registry import ContainerRegistryType
from ai.backend.common.events.dispatcher import EventProducer
from ai.backend.common.plugin.hook import HookPluginContext
from ai.backend.common.types import QuotaScopeID, QuotaScopeType, VFolderUsageMode
from ai.backend.manager.actions.validators import ActionValidators
from ai.backend.manager.api.rest.deployment.handler import DeploymentAPIHandler
from ai.backend.manager.api.rest.deployment.registry import register_deployment_routes
from ai.backend.manager.api.rest.routing import RouteRegistry
from ai.backend.manager.api.rest.types import RouteDeps
from ai.backend.manager.clients.storage_proxy.session_manager import StorageSessionManager
from ai.backend.manager.config.provider import ManagerConfigProvider
from ai.backend.manager.data.image.types import ImageStatus, ImageType
from ai.backend.manager.data.vfolder.types import (
    VFolderMountPermission,
    VFolderOperationStatus,
    VFolderOwnershipType,
)
from ai.backend.manager.dependencies.infrastructure.redis import ValkeyClients
from ai.backend.manager.models.container_registry import ContainerRegistryRow
from ai.backend.manager.models.image.row import ImageRow
from ai.backend.manager.models.utils import ExtendedAsyncSAEngine
from ai.backend.manager.models.vfolder import vfolders
from ai.backend.manager.plugin.network import NetworkPluginContext
from ai.backend.manager.repositories.deployment.repository import DeploymentRepository
from ai.backend.manager.repositories.scheduler import SchedulerRepository
from ai.backend.manager.services.deployment.processors import DeploymentProcessors
from ai.backend.manager.services.deployment.service import DeploymentService
from ai.backend.manager.sokovan.deployment.deployment_controller import (
    DeploymentController,
    DeploymentControllerArgs,
)
from ai.backend.manager.sokovan.deployment.revision_generator.registry import (
    RevisionGeneratorRegistry,
    RevisionGeneratorRegistryArgs,
)
from ai.backend.manager.sokovan.scheduling_controller import (
    SchedulingController,
    SchedulingControllerArgs,
)

# Type aliases for fixture factories
ImageFactoryFunc = Callable[[], Coroutine[Any, Any, uuid.UUID]]
VFolderFactoryFunc = Callable[[], Coroutine[Any, Any, uuid.UUID]]


@pytest.fixture()
def deployment_processors(
    database_engine: ExtendedAsyncSAEngine,
    storage_manager: StorageSessionManager,
    valkey_clients: ValkeyClients,
    config_provider: ManagerConfigProvider,
    event_producer: EventProducer,
    network_plugin_ctx: NetworkPluginContext,
    hook_plugin_ctx: HookPluginContext,
) -> DeploymentProcessors:
    """Real DeploymentProcessors with real DeploymentService and DeploymentRepository."""
    repo = DeploymentRepository(
        database_engine,
        storage_manager,
        valkey_clients.stat,
        valkey_clients.live,
        valkey_clients.schedule,
    )
    scheduler_repository = SchedulerRepository(
        database_engine,
        valkey_clients.stat,
        config_provider,
    )
    scheduling_controller = SchedulingController(
        SchedulingControllerArgs(
            repository=scheduler_repository,
            config_provider=config_provider,
            storage_manager=storage_manager,
            event_producer=event_producer,
            valkey_schedule=valkey_clients.schedule,
            network_plugin_ctx=network_plugin_ctx,
            hook_plugin_ctx=hook_plugin_ctx,
        )
    )
    revision_generator_registry = RevisionGeneratorRegistry(
        RevisionGeneratorRegistryArgs(deployment_repository=repo)
    )
    deployment_controller = DeploymentController(
        DeploymentControllerArgs(
            scheduling_controller=scheduling_controller,
            deployment_repository=repo,
            config_provider=config_provider,
            storage_manager=storage_manager,
            event_producer=event_producer,
            valkey_schedule=valkey_clients.schedule,
            revision_generator_registry=revision_generator_registry,
        )
    )
    service = DeploymentService(deployment_controller, repo, revision_generator_registry)
    return DeploymentProcessors(
        service=service, action_monitors=[], validators=MagicMock(spec=ActionValidators)
    )


@pytest.fixture()
def server_module_registries(
    route_deps: RouteDeps,
    deployment_processors: DeploymentProcessors,
) -> list[RouteRegistry]:
    """Load only the modules required for deployment-domain tests."""
    return [
        register_deployment_routes(
            DeploymentAPIHandler(deployment=deployment_processors), route_deps
        ),
    ]


@pytest.fixture()
async def container_registry_fixture(
    db_engine: SAEngine,
) -> AsyncIterator[uuid.UUID]:
    """Insert a test Docker container registry and yield its UUID."""
    registry_id = uuid.uuid4()
    async with db_engine.begin() as conn:
        await conn.execute(
            sa.insert(ContainerRegistryRow.__table__).values(
                id=registry_id,
                url="https://registry.deployment.test.local",
                registry_name=f"deployment-registry-{registry_id.hex[:8]}",
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
async def image_factory(
    db_engine: SAEngine,
    container_registry_fixture: uuid.UUID,
) -> AsyncIterator[ImageFactoryFunc]:
    """Factory that creates ImageRow entries for deployment tests."""
    created_ids: list[uuid.UUID] = []

    async def _create() -> uuid.UUID:
        image_id = uuid.uuid4()
        unique = secrets.token_hex(4)
        image_name = f"deployment-image-{unique}"
        canonical = f"registry.deployment.test.local/testproject/{image_name}:latest"
        async with db_engine.begin() as conn:
            await conn.execute(
                sa.insert(ImageRow.__table__).values(
                    id=image_id,
                    name=canonical,
                    project="testproject",
                    image=image_name,
                    tag="latest",
                    registry="registry.deployment.test.local",
                    registry_id=container_registry_fixture,
                    architecture="x86_64",
                    config_digest=f"sha256:{image_id.hex * 2}",
                    size_bytes=2048000,
                    is_local=False,
                    type=ImageType.COMPUTE,
                    accelerators=None,
                    labels={},
                    resources={
                        "cpu": {"min": "1", "max": "8"},
                        "mem": {"min": "536870912", "max": "8589934592"},
                    },
                    status=ImageStatus.ALIVE,
                )
            )
        created_ids.append(image_id)
        return image_id

    yield _create

    # Cleanup
    if created_ids:
        async with db_engine.begin() as conn:
            await conn.execute(
                ImageRow.__table__.delete().where(ImageRow.__table__.c.id.in_(created_ids))
            )


@pytest.fixture()
async def vfolder_factory(
    db_engine: SAEngine,
    domain_fixture: str,
    admin_user_fixture: Any,
) -> AsyncIterator[VFolderFactoryFunc]:
    """Factory that creates VFolder entries for deployment model mounts."""
    created_ids: list[uuid.UUID] = []

    async def _create() -> uuid.UUID:
        vfolder_id = uuid.uuid4()
        unique = secrets.token_hex(4)
        user_uuid = admin_user_fixture.user_uuid
        quota_scope_id = QuotaScopeID(
            scope_type=QuotaScopeType.USER,
            scope_id=user_uuid,
        )
        async with db_engine.begin() as conn:
            await conn.execute(
                sa.insert(vfolders).values(
                    id=vfolder_id,
                    name=f"deployment-model-{unique}",
                    host="local",
                    domain_name=domain_fixture,
                    quota_scope_id=str(quota_scope_id),
                    usage_mode=VFolderUsageMode.MODEL,
                    permission=VFolderMountPermission.READ_ONLY,
                    ownership_type=VFolderOwnershipType.USER,
                    user=str(user_uuid),
                    creator="admin-test@test.local",
                    status=VFolderOperationStatus.READY,
                    cloneable=False,
                )
            )
        created_ids.append(vfolder_id)
        return vfolder_id

    yield _create

    # Cleanup
    if created_ids:
        async with db_engine.begin() as conn:
            await conn.execute(vfolders.delete().where(vfolders.c.id.in_(created_ids)))


@pytest.fixture()
async def deployment_seed_data(
    image_factory: ImageFactoryFunc,
    vfolder_factory: VFolderFactoryFunc,
) -> tuple[uuid.UUID, uuid.UUID]:
    """Create and return (image_id, vfolder_id) for deployment tests."""
    image_id = await image_factory()
    vfolder_id = await vfolder_factory()
    return image_id, vfolder_id
