from __future__ import annotations

import uuid
from collections.abc import Iterator
from typing import cast
from unittest.mock import AsyncMock, MagicMock

import pytest

from ai.backend.common.bgtask.bgtask import BackgroundTaskManager
from ai.backend.common.contexts.user import with_user
from ai.backend.common.data.user.types import UserData, UserRole
from ai.backend.common.events.dispatcher import EventDispatcher
from ai.backend.common.events.hub import EventHub
from ai.backend.common.types import AccessKey, ClusterMode, RuntimeVariant
from ai.backend.manager.actions.monitors.monitor import ActionMonitor
from ai.backend.manager.clients.storage_proxy.session_manager import StorageSessionManager
from ai.backend.manager.config.provider import ManagerConfigProvider
from ai.backend.manager.data.model_serving.types import ModelServicePrepareCtx, ServiceConfig
from ai.backend.manager.repositories.model_serving.repositories import ModelServingRepositories
from ai.backend.manager.repositories.model_serving.repository import ModelServingRepository
from ai.backend.manager.services.model_serving.actions.dry_run_model_service import (
    DryRunModelServiceAction,
    DryRunModelServiceActionResult,
)
from ai.backend.manager.services.model_serving.processors.model_serving import (
    ModelServingProcessors,
)
from ai.backend.manager.services.model_serving.services.model_serving import ModelServingService
from ai.backend.manager.sokovan.deployment.deployment_controller import DeploymentController
from ai.backend.manager.sokovan.scheduling_controller import SchedulingController
from ai.backend.testutils.scenario import ScenarioBase


class TestDryRunModelService:
    @pytest.fixture
    def user_data(self) -> UserData:
        return UserData(
            user_id=uuid.UUID("00000000-0000-0000-0000-000000000001"),
            is_authorized=True,
            is_admin=False,
            is_superadmin=False,
            role=UserRole.USER,
            domain_name="default",
        )

    @pytest.fixture(autouse=True)
    def set_user_context(self, user_data: UserData) -> Iterator[None]:
        with with_user(user_data):
            yield

    @pytest.fixture
    def mock_storage_manager(self) -> MagicMock:
        return MagicMock(spec=StorageSessionManager)

    @pytest.fixture
    def mock_action_monitor(self) -> MagicMock:
        return MagicMock(spec=ActionMonitor)

    @pytest.fixture
    def mock_event_dispatcher(self) -> MagicMock:
        mock = MagicMock(spec=EventDispatcher)
        mock.dispatch = AsyncMock()
        return mock

    @pytest.fixture
    def mock_agent_registry(self) -> MagicMock:
        return MagicMock()

    @pytest.fixture
    def mock_config_provider(self) -> MagicMock:
        return MagicMock(spec=ManagerConfigProvider)

    @pytest.fixture
    def mock_repositories(self) -> MagicMock:
        mock = MagicMock(spec=ModelServingRepositories)
        mock.repository = MagicMock(spec=ModelServingRepository)
        return mock

    @pytest.fixture
    def mock_background_task_manager(self) -> MagicMock:
        return MagicMock(spec=BackgroundTaskManager)

    @pytest.fixture
    def mock_valkey_live(self) -> MagicMock:
        mock = MagicMock()
        mock.store_live_data = AsyncMock()
        mock.get_live_data = AsyncMock()
        mock.delete_live_data = AsyncMock()
        return mock

    @pytest.fixture
    def mock_deployment_controller(self) -> MagicMock:
        mock = MagicMock(spec=DeploymentController)
        mock.mark_lifecycle_needed = AsyncMock()
        return mock

    @pytest.fixture
    def mock_event_hub(self) -> MagicMock:
        mock = MagicMock(spec=EventHub)
        mock.register_event_propagator = MagicMock()
        mock.unregister_event_propagator = MagicMock()
        return mock

    @pytest.fixture
    def mock_scheduling_controller(self) -> MagicMock:
        mock = MagicMock(spec=SchedulingController)
        mock.enqueue_session = AsyncMock()
        mock.mark_sessions_for_termination = AsyncMock()
        return mock

    @pytest.fixture
    def model_serving_service(
        self,
        mock_storage_manager: MagicMock,
        mock_event_dispatcher: MagicMock,
        mock_event_hub: MagicMock,
        mock_agent_registry: MagicMock,
        mock_background_task_manager: MagicMock,
        mock_config_provider: MagicMock,
        mock_valkey_live: MagicMock,
        mock_repositories: MagicMock,
        mock_deployment_controller: MagicMock,
        mock_scheduling_controller: MagicMock,
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
            deployment_controller=mock_deployment_controller,
            scheduling_controller=mock_scheduling_controller,
        )

    @pytest.fixture
    def model_serving_processors(
        self,
        mock_action_monitor: MagicMock,
        model_serving_service: ModelServingService,
    ) -> ModelServingProcessors:
        return ModelServingProcessors(
            service=model_serving_service,
            action_monitors=[mock_action_monitor],
        )

    @pytest.fixture
    def mock_get_vfolder_by_id_dry_run(self, mocker, mock_repositories) -> MagicMock:
        mock = mocker.patch.object(
            mock_repositories.repository,
            "get_vfolder_by_id",
            new_callable=MagicMock,
        )
        mock.return_value = MagicMock(id=uuid.uuid4())
        return mock

    @pytest.fixture
    def mock_get_user_with_keypair(self, mocker, mock_repositories) -> AsyncMock:
        return mocker.patch.object(
            mock_repositories.repository,
            "get_user_with_keypair",
            new_callable=AsyncMock,
        )

    @pytest.fixture
    def mock_resolve_image_for_endpoint_creation_dry_run(
        self, mocker, mock_repositories
    ) -> AsyncMock:
        mock = mocker.patch.object(
            mock_repositories.repository,
            "resolve_image_for_endpoint_creation",
            new_callable=AsyncMock,
        )
        mock.return_value = MagicMock(image_ref="test-image:latest")
        return mock

    @pytest.fixture
    def mock_background_task_manager_start(self, mocker, mock_background_task_manager) -> AsyncMock:
        return mocker.patch.object(
            mock_background_task_manager,
            "start",
            new_callable=AsyncMock,
        )

    @pytest.mark.parametrize(
        "scenario",
        [
            ScenarioBase.success(
                "Configuration validation success",
                DryRunModelServiceAction(
                    service_name="test-model-v1.0",
                    replicas=2,
                    image="ai.backend/python:3.9",
                    runtime_variant=RuntimeVariant.CUSTOM,
                    architecture="x86_64",
                    group_name="group1",
                    domain_name="default",
                    cluster_size=1,
                    cluster_mode=ClusterMode.SINGLE_NODE,
                    tag=None,
                    startup_command=None,
                    bootstrap_script=None,
                    callback_url=None,
                    owner_access_key=None,
                    open_to_public=False,
                    config=ServiceConfig(
                        model="test-model",
                        model_definition_path=None,
                        model_version=1,
                        model_mount_destination="/models",
                        extra_mounts={},
                        environ={},
                        scaling_group="default",
                        resources={"cpu": "2", "memory": "4G"},
                        resource_opts={},
                    ),
                    request_user_id=uuid.UUID("00000000-0000-0000-0000-000000000001"),
                    sudo_session_enabled=False,
                    model_service_prepare_ctx=ModelServicePrepareCtx(
                        model_id=uuid.UUID("77777777-7777-7777-7777-777777777777"),
                        model_definition_path=None,
                        requester_access_key=AccessKey("ACCESSKEY001"),
                        owner_access_key=AccessKey("ACCESSKEY001"),
                        owner_uuid=uuid.UUID("00000000-0000-0000-0000-000000000001"),
                        owner_role=UserRole.USER,
                        group_id=uuid.UUID("00000000-0000-0000-0000-000000000002"),
                        resource_policy={},
                        scaling_group="default",
                        extra_mounts=[],
                    ),
                ),
                DryRunModelServiceActionResult(
                    task_id=uuid.UUID("aaaaaaaa-aaaa-aaaa-aaaa-aaaaaaaaaaaa"),
                ),
            ),
        ],
    )
    @pytest.mark.asyncio
    async def test_dry_run_model_service(
        self,
        scenario: ScenarioBase[DryRunModelServiceAction, DryRunModelServiceActionResult],
        model_serving_processors: ModelServingProcessors,
        mock_get_vfolder_by_id_dry_run,
        mock_get_user_with_keypair,
        mock_resolve_image_for_endpoint_creation_dry_run,
        mock_background_task_manager_start,
    ):
        mock_get_user_with_keypair.return_value = MagicMock(
            uuid=scenario.input.model_service_prepare_ctx.owner_uuid,
            role=scenario.input.model_service_prepare_ctx.owner_role,
        )

        expected = cast(DryRunModelServiceActionResult, scenario.expected)
        mock_background_task_manager_start.return_value = expected.task_id

        async def dry_run_model_service(action: DryRunModelServiceAction):
            return await model_serving_processors.dry_run_model_service.wait_for_complete(action)

        await scenario.test(dry_run_model_service)
