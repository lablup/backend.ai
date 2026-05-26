from __future__ import annotations

import secrets
import uuid
from collections.abc import AsyncIterator, Callable, Coroutine
from typing import Any
from unittest.mock import AsyncMock, MagicMock

import pytest
import sqlalchemy as sa
from sqlalchemy.ext.asyncio.engine import AsyncEngine as SAEngine

from ai.backend.common.container_registry import ContainerRegistryType
from ai.backend.common.events.dispatcher import EventProducer
from ai.backend.common.identifier.image import ImageID
from ai.backend.common.identifier.runtime_variant import RuntimeVariantID
from ai.backend.common.identifier.vfolder import VFolderUUID
from ai.backend.common.plugin.hook import HookPluginContext
from ai.backend.common.types import QuotaScopeID, QuotaScopeType, VFolderUsageMode
from ai.backend.manager.actions.validators import ActionValidators
from ai.backend.manager.actions.validators.rbac import RBACValidators
from ai.backend.manager.actions.validators.rbac.bulk import BulkActionRBACValidator
from ai.backend.manager.actions.validators.rbac.scope import ScopeActionRBACValidator
from ai.backend.manager.actions.validators.rbac.single_entity import (
    SingleEntityActionRBACValidator,
)
from ai.backend.manager.api.adapters.runtime_variant.adapter import RuntimeVariantAdapter
from ai.backend.manager.api.rest.deployment.handler import DeploymentAPIHandler
from ai.backend.manager.api.rest.deployment.registry import register_deployment_routes
from ai.backend.manager.api.rest.routing import RouteRegistry
from ai.backend.manager.api.rest.types import RouteDeps
from ai.backend.manager.clients.appproxy.client import AppProxyClientPool
from ai.backend.manager.clients.storage_proxy.session_manager import StorageSessionManager
from ai.backend.manager.config.provider import ManagerConfigProvider
from ai.backend.manager.data.image.types import ImageStatus, ImageType
from ai.backend.manager.data.permission.status import RoleStatus
from ai.backend.manager.data.permission.types import EntityType, OperationType, ScopeType
from ai.backend.manager.data.vfolder.types import (
    VFolderMountPermission,
    VFolderOperationStatus,
    VFolderOwnershipType,
)
from ai.backend.manager.dependencies.infrastructure.redis import ValkeyClients
from ai.backend.manager.models.container_registry import ContainerRegistryRow
from ai.backend.manager.models.deployment_policy.row import DeploymentPolicyRow
from ai.backend.manager.models.deployment_revision.row import DeploymentRevisionRow
from ai.backend.manager.models.endpoint.row import EndpointRow
from ai.backend.manager.models.image.row import ImageRow
from ai.backend.manager.models.rbac_models.permission.permission import PermissionRow
from ai.backend.manager.models.rbac_models.role import RoleRow
from ai.backend.manager.models.rbac_models.user_role import UserRoleRow
from ai.backend.manager.models.utils import ExtendedAsyncSAEngine
from ai.backend.manager.models.vfolder import vfolders
from ai.backend.manager.plugin.network import NetworkPluginContext
from ai.backend.manager.repositories.deployment.repository import DeploymentRepository
from ai.backend.manager.repositories.permission_controller.repository import (
    PermissionControllerRepository,
)
from ai.backend.manager.repositories.scheduler import SchedulerRepository
from ai.backend.manager.services.deployment.processors import DeploymentProcessors
from ai.backend.manager.services.deployment.service import DeploymentService
from ai.backend.manager.sokovan.deployment.deployment_controller import (
    DeploymentController,
    DeploymentControllerArgs,
)
from ai.backend.manager.sokovan.deployment.revision_draft import RevisionDraftReader
from ai.backend.manager.sokovan.scheduling_controller import (
    SchedulingController,
    SchedulingControllerArgs,
)
from ai.backend.testutils.fixtures import DomainFixtureData

# Type aliases for fixture factories
ImageFactoryFunc = Callable[[], Coroutine[Any, Any, ImageID]]
VFolderFactoryFunc = Callable[[], Coroutine[Any, Any, VFolderUUID]]


@pytest.fixture(autouse=True)
async def _seed_resource_slot_types(db_engine: SAEngine) -> None:
    """Ensure resource_slot_types has seed data for FK constraints."""
    async with db_engine.begin() as conn:
        await conn.execute(
            sa.text(
                "INSERT INTO resource_slot_types (slot_name, slot_type, rank)"
                " VALUES ('cpu', 'count', 40), ('mem', 'bytes', 50)"
                " ON CONFLICT DO NOTHING"
            )
        )


@pytest.fixture()
def mock_appproxy_client_pool() -> MagicMock:
    """Stub AppProxyClientPool for tests that do not exercise app-proxy IO."""
    return MagicMock(spec=AppProxyClientPool)


@pytest.fixture()
def deployment_processors(
    database_engine: ExtendedAsyncSAEngine,
    storage_manager: StorageSessionManager,
    valkey_clients: ValkeyClients,
    config_provider: ManagerConfigProvider,
    event_producer: EventProducer,
    network_plugin_ctx: NetworkPluginContext,
    hook_plugin_ctx: HookPluginContext,
    mock_appproxy_client_pool: MagicMock,
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
    revision_draft_reader = RevisionDraftReader(deployment_repository=repo)
    deployment_controller = DeploymentController(
        DeploymentControllerArgs(
            scheduling_controller=scheduling_controller,
            deployment_repository=repo,
            config_provider=config_provider,
            storage_manager=storage_manager,
            event_producer=event_producer,
            valkey_schedule=valkey_clients.schedule,
            revision_draft_reader=revision_draft_reader,
            deployment_revision_preset_repository=None,
        )
    )
    service = DeploymentService(
        deployment_controller,
        repo,
        appproxy_client_pool=mock_appproxy_client_pool,
    )
    permission_controller_repo = PermissionControllerRepository(database_engine)
    return DeploymentProcessors(
        service=service,
        action_monitors=[],
        validators=ActionValidators(
            rbac=RBACValidators(
                scope=ScopeActionRBACValidator(permission_controller_repo, MagicMock()),
                single_entity=SingleEntityActionRBACValidator(
                    permission_controller_repo, MagicMock()
                ),
                bulk=BulkActionRBACValidator(permission_controller_repo, MagicMock()),
            ),
        ),
    )


@pytest.fixture()
async def regular_user_project_model_deployment_read_permission(
    db_engine: SAEngine,
    regular_user_fixture: Any,
    group_fixture: uuid.UUID,
) -> AsyncIterator[None]:
    """Grant PROJECT-scoped MODEL_DEPLOYMENT:READ permission to the regular user."""
    role_id = uuid.uuid4()
    async with db_engine.begin() as conn:
        await conn.execute(
            sa.insert(RoleRow.__table__).values(
                id=role_id,
                name=f"test-deployment-reader-{secrets.token_hex(4)}",
                status=RoleStatus.ACTIVE,
            )
        )
        await conn.execute(
            sa.insert(UserRoleRow.__table__).values(
                user_id=regular_user_fixture.user_uuid,
                role_id=role_id,
            )
        )
        await conn.execute(
            sa.insert(PermissionRow.__table__).values(
                role_id=role_id,
                scope_type=ScopeType.PROJECT,
                scope_id=str(group_fixture),
                entity_type=EntityType.MODEL_DEPLOYMENT,
                operation=OperationType.READ,
            )
        )
    yield
    async with db_engine.begin() as conn:
        await conn.execute(
            PermissionRow.__table__.delete().where(PermissionRow.__table__.c.role_id == role_id)
        )
        await conn.execute(
            UserRoleRow.__table__.delete().where(UserRoleRow.__table__.c.role_id == role_id)
        )
        await conn.execute(RoleRow.__table__.delete().where(RoleRow.__table__.c.id == role_id))


@pytest.fixture()
async def runtime_variant_fixture(
    db_engine: SAEngine,
) -> AsyncIterator[uuid.UUID]:
    """Seed a runtime_variant row so deployment creates can resolve its FK."""
    variant_id = uuid.uuid4()
    default_definition = (
        '{"models": [{"name": "test-model", "model_path": "/models/test",'
        ' "service": {"start_command": ["python", "serve.py"], "port": 8000}}]}'
    )
    async with db_engine.begin() as conn:
        await conn.execute(
            sa.text(
                "INSERT INTO runtime_variants (id, name, description, default_model_definition)"
                " VALUES (:id, :name, :desc, CAST(:default_model_definition AS jsonb))"
            ).bindparams(
                id=variant_id,
                name=f"test-variant-{variant_id.hex[:8]}",
                desc="Test runtime variant for deployment tests",
                default_model_definition=default_definition,
            )
        )
    yield variant_id
    async with db_engine.begin() as conn:
        await conn.execute(
            sa.text("DELETE FROM runtime_variants WHERE id = :id").bindparams(id=variant_id)
        )


@pytest.fixture()
def server_module_registries(
    route_deps: RouteDeps,
    deployment_processors: DeploymentProcessors,
    runtime_variant_fixture: uuid.UUID,
) -> list[RouteRegistry]:
    """Load only the modules required for deployment-domain tests."""
    resolved_variant_id = RuntimeVariantID(runtime_variant_fixture)
    runtime_variant_adapter = MagicMock(spec=RuntimeVariantAdapter)
    runtime_variant_adapter.resolve_by_name = AsyncMock(return_value=resolved_variant_id)
    _variant_node_mock = MagicMock()
    _variant_node_mock.name = "custom"
    runtime_variant_adapter.get = AsyncMock(return_value=_variant_node_mock)
    return [
        register_deployment_routes(
            DeploymentAPIHandler(
                deployment=deployment_processors,
                runtime_variant_adapter=runtime_variant_adapter,
            ),
            route_deps,
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
    created_ids: list[ImageID] = []

    async def _create() -> ImageID:
        image_id = ImageID(uuid.uuid4())
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
    domain_fixture: DomainFixtureData,
    admin_user_fixture: Any,
) -> AsyncIterator[VFolderFactoryFunc]:
    """Factory that creates VFolder entries for deployment model mounts."""
    created_ids: list[VFolderUUID] = []

    async def _create() -> VFolderUUID:
        vfolder_id = VFolderUUID(uuid.uuid4())
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
                    domain_name=domain_fixture.domain_name,
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
    db_engine: SAEngine,
    domain_fixture: DomainFixtureData,
    image_factory: ImageFactoryFunc,
    vfolder_factory: VFolderFactoryFunc,
) -> AsyncIterator[tuple[ImageID, VFolderUUID]]:
    """Create seed data and clean up endpoints created during the test.

    Endpoints reference domains/groups/scaling_groups with RESTRICT FK,
    so they must be removed before those fixture teardowns run.
    This fixture is torn down before group/scaling_group/domain fixtures
    because it transitively depends on them via image_factory and vfolder_factory.
    """
    image_id = await image_factory()
    vfolder_id = await vfolder_factory()
    yield image_id, vfolder_id
    # Clean up endpoints and soft-FK children created during the test
    async with db_engine.begin() as conn:
        endpoint_ids_q = sa.select(EndpointRow.__table__.c.id).where(
            EndpointRow.__table__.c.domain == domain_fixture.domain_name
        )
        await conn.execute(
            DeploymentRevisionRow.__table__.delete().where(
                DeploymentRevisionRow.__table__.c.endpoint.in_(endpoint_ids_q)
            )
        )
        await conn.execute(
            DeploymentPolicyRow.__table__.delete().where(
                DeploymentPolicyRow.__table__.c.endpoint.in_(endpoint_ids_q)
            )
        )
        await conn.execute(
            EndpointRow.__table__.delete().where(
                EndpointRow.__table__.c.domain == domain_fixture.domain_name
            )
        )
