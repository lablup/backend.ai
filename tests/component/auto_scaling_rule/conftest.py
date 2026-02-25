from __future__ import annotations

import uuid
from collections.abc import AsyncIterator
from contextlib import asynccontextmanager
from dataclasses import dataclass
from unittest.mock import AsyncMock, MagicMock

import pytest
import sqlalchemy as sa
from sqlalchemy.ext.asyncio.engine import AsyncEngine as SAEngine

from ai.backend.common.container_registry import ContainerRegistryType
from ai.backend.common.data.endpoint.types import EndpointLifecycle
from ai.backend.common.types import ResourceSlot
from ai.backend.manager.api import ManagerStatus
from ai.backend.manager.api import auth as _auth_api
from ai.backend.manager.api import auto_scaling_rule as _auto_scaling_rule_api
from ai.backend.manager.api.context import RootContext
from ai.backend.manager.api.types import CleanupContext
from ai.backend.manager.data.image.types import ImageType
from ai.backend.manager.models.container_registry.row import ContainerRegistryRow
from ai.backend.manager.models.endpoint import EndpointRow
from ai.backend.manager.models.image import ImageRow
from ai.backend.manager.repositories.deployment.repository import DeploymentRepository
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
from ai.backend.manager.services.deployment.processors import DeploymentProcessors
from ai.backend.manager.services.deployment.service import DeploymentService
from ai.backend.manager.services.processors import ProcessorArgs, Processors, ServiceArgs


@dataclass
class KeypairFixtureData:
    access_key: str
    secret_key: str


@dataclass
class UserFixtureData:
    user_uuid: uuid.UUID
    keypair: KeypairFixtureData
    email: str = ""


# Statically imported so that Pants includes these modules in the test PEX.
# build_root_app() loads them at runtime via importlib.import_module(),
# which Pants cannot trace statically.
_AUTO_SCALING_RULE_SERVER_SUBAPP_MODULES = (_auth_api, _auto_scaling_rule_api)


@asynccontextmanager
async def _auto_scaling_rule_domain_ctx(root_ctx: RootContext) -> AsyncIterator[None]:
    """Set up repositories and processors for auto-scaling-rule-domain component tests.

    Relies on the preceding cleanup contexts having already initialized:
    - redis_ctx      → root_ctx.valkey_* (all 8 clients)
    - database_ctx   → root_ctx.db
    - monitoring_ctx → root_ctx.error_monitor / stats_monitor
    - storage_manager_ctx  → root_ctx.storage_manager
    - message_queue_ctx    → root_ctx.message_queue
    - event_producer_ctx   → root_ctx.event_producer / event_fetcher
    - event_hub_ctx        → root_ctx.event_hub
    - background_task_ctx  → root_ctx.background_task_manager

    The standard pattern (deployment_controller=MagicMock()) leaves the
    DeploymentService with a MagicMock repository, breaking all async calls.
    We fix this by creating a real DeploymentRepository and overriding
    root_ctx.processors.deployment after Processors.create().
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

    # Override the deployment processors with a real DeploymentRepository
    # so that auto-scaling rule service methods can execute real DB queries.
    deployment_repo = DeploymentRepository(
        db=root_ctx.db,
        storage_manager=root_ctx.storage_manager,
        valkey_stat=root_ctx.valkey_stat,
        valkey_live=root_ctx.valkey_live,
        valkey_schedule=root_ctx.valkey_schedule,
    )
    deployment_service = DeploymentService(
        deployment_controller=MagicMock(),
        deployment_repository=deployment_repo,
    )
    root_ctx.processors.deployment = DeploymentProcessors(deployment_service, [])
    yield


@pytest.fixture()
def server_subapp_pkgs() -> list[str]:
    """Load only the subapps required for auto-scaling-rule-domain tests."""
    return [".auth", ".auto_scaling_rule"]


@pytest.fixture()
def server_cleanup_contexts() -> list[CleanupContext]:
    """Provide cleanup contexts for auto-scaling-rule-domain component tests."""
    return [
        redis_ctx,
        database_ctx,
        monitoring_ctx,
        storage_manager_ctx,
        message_queue_ctx,
        event_producer_ctx,
        event_hub_ctx,
        background_task_ctx,
        _auto_scaling_rule_domain_ctx,
    ]


@pytest.fixture()
async def model_deployment_fixture(
    db_engine: SAEngine,
    domain_fixture: str,
    group_fixture: uuid.UUID,
    scaling_group_fixture: str,
    admin_user_fixture: UserFixtureData,
) -> AsyncIterator[uuid.UUID]:
    """Insert a minimal EndpointRow (model deployment) and yield its UUID.

    Creates required prerequisite rows (ContainerRegistryRow, ImageRow)
    since the database_fixture does not seed them.
    """
    registry_id = uuid.uuid4()
    image_id = uuid.uuid4()
    endpoint_id = uuid.uuid4()

    async with db_engine.begin() as conn:
        # Insert a minimal container registry
        await conn.execute(
            sa.insert(ContainerRegistryRow.__table__).values(
                id=registry_id,
                url="http://test-registry.local",
                registry_name="test-registry",
                type=ContainerRegistryType.DOCKER,
                project=None,
            )
        )
        # Insert a minimal image
        await conn.execute(
            sa.insert(ImageRow.__table__).values(
                id=image_id,
                name="test-image",
                project=None,
                image="test-image:latest",
                tag="latest",
                registry="test-registry",
                registry_id=registry_id,
                architecture="x86_64",
                config_digest="sha256:" + "0" * 64,
                size_bytes=1024,
                is_local=False,
                type=ImageType.COMPUTE,
                labels={},
                resources={"cpu": {"min": "1"}, "mem": {"min": "268435456"}},
            )
        )
        # Insert a minimal endpoint (model deployment)
        await conn.execute(
            sa.insert(EndpointRow.__table__).values(
                id=endpoint_id,
                name=f"test-endpoint-{uuid.uuid4().hex[:8]}",
                created_user=str(admin_user_fixture.user_uuid),
                session_owner=str(admin_user_fixture.user_uuid),
                domain=domain_fixture,
                project=str(group_fixture),
                resource_group=scaling_group_fixture,
                image=image_id,
                lifecycle_stage=EndpointLifecycle.CREATED.value,
                resource_slots=ResourceSlot({"cpu": "1", "mem": "1073741824"}),
                url=None,
            )
        )
    yield endpoint_id
    async with db_engine.begin() as conn:
        # Delete in reverse FK order
        await conn.execute(
            sa.delete(EndpointRow.__table__).where(EndpointRow.__table__.c.id == endpoint_id)
        )
        await conn.execute(sa.delete(ImageRow.__table__).where(ImageRow.__table__.c.id == image_id))
        await conn.execute(
            sa.delete(ContainerRegistryRow.__table__).where(
                ContainerRegistryRow.__table__.c.id == registry_id
            )
        )
