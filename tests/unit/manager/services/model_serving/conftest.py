import uuid
from contextlib import asynccontextmanager
from datetime import datetime
from typing import AsyncGenerator
from unittest.mock import AsyncMock, MagicMock

import pytest
import sqlalchemy as sa

from ai.backend.common.bgtask.bgtask import BackgroundTaskManager
from ai.backend.common.clients.valkey_client.valkey_stat.client import ValkeyStatClient
from ai.backend.common.data.endpoint.types import EndpointStatus
from ai.backend.common.events.dispatcher import EventDispatcher
from ai.backend.common.events.hub import EventHub
from ai.backend.manager.actions.monitors.monitor import ActionMonitor
from ai.backend.manager.config.provider import ManagerConfigProvider
from ai.backend.manager.models.endpoint import (
    EndpointLifecycle,
    EndpointRow,
)
from ai.backend.manager.models.storage import StorageSessionManager
from ai.backend.manager.models.utils import ExtendedAsyncSAEngine
from ai.backend.manager.models.vfolder import VFolderOwnershipType, VFolderRow
from ai.backend.manager.registry import AgentRegistry
from ai.backend.manager.repositories.model_serving.admin_repository import (
    AdminModelServingRepository,
)
from ai.backend.manager.repositories.model_serving.repositories import ModelServingRepositories
from ai.backend.manager.repositories.model_serving.repository import ModelServingRepository
from ai.backend.manager.services.model_serving.processors.auto_scaling import (
    ModelServingAutoScalingProcessors,
)
from ai.backend.manager.services.model_serving.processors.model_serving import (
    ModelServingProcessors,
)
from ai.backend.manager.services.model_serving.services.auto_scaling import AutoScalingService
from ai.backend.manager.services.model_serving.services.model_serving import ModelServingService
from ai.backend.manager.sokovan.deployment.deployment_controller import DeploymentController
from ai.backend.manager.sokovan.scheduling_controller import SchedulingController


@pytest.fixture
def mock_redis_connection():
    mock_redis_connection = MagicMock(spec=ValkeyStatClient)
    return mock_redis_connection


@pytest.fixture
def mock_storage_manager():
    mock_storage_manager = MagicMock(spec=StorageSessionManager)
    return mock_storage_manager


@pytest.fixture
def mock_action_monitor():
    mock_action_monitor = MagicMock(spec=ActionMonitor)
    return mock_action_monitor


@pytest.fixture
def mock_event_dispatcher():
    mock_event_dispatcher = MagicMock(spec=EventDispatcher)
    mock_event_dispatcher.dispatch = AsyncMock()
    return mock_event_dispatcher


@pytest.fixture
def mock_agent_registry():
    mock_agent_registry = MagicMock(spec=AgentRegistry)
    return mock_agent_registry


@pytest.fixture
def mock_config_provider():
    mock_config_provider = MagicMock(spec=ManagerConfigProvider)
    return mock_config_provider


@pytest.fixture
def mock_repositories():
    mock_repositories = MagicMock(spec=ModelServingRepositories)
    mock_repositories.repository = MagicMock(spec=ModelServingRepository)
    mock_repositories.admin_repository = MagicMock(spec=AdminModelServingRepository)
    return mock_repositories


@pytest.fixture
def mock_background_task_manager():
    mock_background_task_manager = MagicMock(spec=BackgroundTaskManager)
    return mock_background_task_manager


@pytest.fixture
def mock_valkey_live():
    mock = MagicMock()
    mock.store_live_data = AsyncMock()
    mock.get_live_data = AsyncMock()
    mock.delete_live_data = AsyncMock()
    return mock


@pytest.fixture
def mock_deployment_controller():
    mock_deployment_controller = MagicMock(spec=DeploymentController)
    mock_deployment_controller.mark_lifecycle_needed = AsyncMock()
    return mock_deployment_controller


@pytest.fixture
def mock_event_hub():
    mock_event_hub = MagicMock(spec=EventHub)
    mock_event_hub.register_event_propagator = MagicMock()
    mock_event_hub.unregister_event_propagator = MagicMock()
    return mock_event_hub


@pytest.fixture
def mock_scheduling_controller():
    mock_scheduling_controller = MagicMock(spec=SchedulingController)
    mock_scheduling_controller.enqueue_session = AsyncMock()
    mock_scheduling_controller.mark_sessions_for_termination = AsyncMock()
    return mock_scheduling_controller


@pytest.fixture
def model_serving_service(
    database_fixture,
    database_engine,
    mock_storage_manager,
    mock_event_dispatcher,
    mock_event_hub,
    mock_agent_registry,
    mock_background_task_manager,
    mock_config_provider,
    mock_valkey_live,
    mock_repositories,
    mock_deployment_controller,
    mock_scheduling_controller,
) -> ModelServingService:
    return ModelServingService(
        agent_registry=mock_agent_registry,
        background_task_manager=mock_background_task_manager,
        event_dispatcher=mock_event_dispatcher,
        event_hub=mock_event_hub,
        storage_manager=mock_storage_manager,
        config_provider=mock_config_provider,
        valkey_live=mock_valkey_live,
        repository=mock_repositories.repository,
        admin_repository=mock_repositories.admin_repository,
        deployment_controller=mock_deployment_controller,
        scheduling_controller=mock_scheduling_controller,
    )


@pytest.fixture
def model_serving_processors(
    database_fixture,
    database_engine,
    mock_action_monitor,
    model_serving_service,
) -> ModelServingProcessors:
    return ModelServingProcessors(
        service=model_serving_service,
        action_monitors=[mock_action_monitor],
    )


@pytest.fixture
def auto_scaling_service(
    mock_repositories,
):
    return AutoScalingService(
        repository=mock_repositories.repository,
        admin_repository=mock_repositories.admin_repository,
    )


@pytest.fixture
def auto_scaling_processors(
    database_fixture,
    database_engine,
    mock_action_monitor,
    auto_scaling_service,
) -> ModelServingAutoScalingProcessors:
    return ModelServingAutoScalingProcessors(
        service=auto_scaling_service,
        action_monitors=[mock_action_monitor],
    )


@pytest.fixture
def create_vfolder(
    database_engine: ExtendedAsyncSAEngine,
):
    @asynccontextmanager
    async def _create_vfolder(
        vfolder_id: uuid.UUID,
        name: str,
        user_uuid: uuid.UUID,
        domain_name: str,
        ownership_type: VFolderOwnershipType = VFolderOwnershipType.USER,
    ) -> AsyncGenerator[uuid.UUID, None]:
        async with database_engine.begin_session() as session:
            vfolder_data = {
                "id": vfolder_id,
                "name": name,
                "user": user_uuid,
                "domain_name": domain_name,
                "ownership_type": ownership_type,
                "max_files": 1000,
                "max_size": 1073741824,  # 1GB
                "num_files": 0,
                "cur_size": 0,
                "created_at": datetime.utcnow(),
                "last_used": None,
                "unmanaged_path": "",
                "usage_mode": "general",
                "permission": "rw",
                "last_size_update": datetime.utcnow(),
                "status": "ready",
            }
            await session.execute(sa.insert(VFolderRow).values(vfolder_data))
        try:
            yield vfolder_id
        finally:
            async with database_engine.begin_session() as session:
                await session.execute(sa.delete(VFolderRow).where(VFolderRow.id == vfolder_id))

    return _create_vfolder


@pytest.fixture
def create_endpoint(
    database_engine: ExtendedAsyncSAEngine,
):
    @asynccontextmanager
    async def _create_endpoint(
        endpoint_id: uuid.UUID,
        model_name: str,
        model_version: str,
        domain_name: str,
        owner_uuid: uuid.UUID,
        status: EndpointStatus = EndpointStatus.READY,
        lifecycle_stage: EndpointLifecycle = EndpointLifecycle.CREATED,
    ) -> AsyncGenerator[uuid.UUID, None]:
        async with database_engine.begin_session() as session:
            endpoint_data = {
                "id": endpoint_id,
                "name": f"{model_name}-{model_version}",
                "model_name": model_name,
                "model_version": model_version,
                "domain": domain_name,
                "project": None,
                "owner": owner_uuid,
                "url": f"https://api.example.com/v1/models/{model_name}/{model_version}",
                "retries": 0,
                "status": status,
                "lifecycle_stage": lifecycle_stage,
                "open_to_public": False,
                "config": {},
                "runtime_variant": "custom",
                "resource_group": "default",
                "tag": None,
                "environ": {},
                "bootstrap_script": None,
                "callback_url": None,
                "startup_command": None,
                "created_at": datetime.utcnow(),
                "destroyed_at": None,
            }
            await session.execute(sa.insert(EndpointRow).values(endpoint_data))
        try:
            yield endpoint_id
        finally:
            async with database_engine.begin_session() as session:
                await session.execute(sa.delete(EndpointRow).where(EndpointRow.id == endpoint_id))

    return _create_endpoint
