from __future__ import annotations

import uuid
from collections.abc import Iterator
from typing import cast, Any
from unittest.mock import AsyncMock, MagicMock

import pytest
from pydantic import HttpUrl

from ai.backend.common.bgtask.bgtask import BackgroundTaskManager
from ai.backend.common.contexts.user import with_user
from ai.backend.common.data.user.types import UserData, UserRole
from ai.backend.common.events.dispatcher import EventDispatcher
from ai.backend.common.events.hub import EventHub
from ai.backend.common.types import RuntimeVariant
from ai.backend.manager.actions.monitors.monitor import ActionMonitor
from ai.backend.manager.clients.storage_proxy.session_manager import StorageSessionManager
from ai.backend.manager.config.provider import ManagerConfigProvider
from ai.backend.manager.data.model_serving.types import ServiceInfo
from ai.backend.manager.repositories.model_serving.repositories import ModelServingRepositories
from ai.backend.manager.repositories.model_serving.repository import ModelServingRepository
from ai.backend.manager.services.model_serving.actions.get_model_service_info import (
    GetModelServiceInfoAction,
    GetModelServiceInfoActionResult,
)
from ai.backend.manager.services.model_serving.processors.model_serving import (
    ModelServingProcessors,
)
from ai.backend.manager.services.model_serving.services.model_serving import ModelServingService
from ai.backend.manager.sokovan.deployment.deployment_controller import DeploymentController
from ai.backend.manager.sokovan.scheduling_controller import SchedulingController
from ai.backend.testutils.scenario import ScenarioBase


class TestGetModelServiceInfo:
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
    def mock_check_user_access_get_info(self, mocker: Any, model_serving_service: Any)-> AsyncMock:
        mock = mocker.patch.object(
            model_serving_service,
            "check_user_access",
            new_callable=AsyncMock,
        )
        mock.return_value = None
        return mock

    @pytest.fixture
    def mock_get_endpoint_by_id_get_info(self, mocker: Any, mock_repositories: Any)-> AsyncMock:
        return mocker.patch.object(
            mock_repositories.repository,
            "get_endpoint_by_id",
            new_callable=AsyncMock,
        )

    @pytest.fixture
    def mock_get_endpoint_access_validation_data_get_info(
        self, mocker: Any, mock_repositories: Any
    ) -> AsyncMock:
        return mocker.patch.object(
            mock_repositories.repository,
            "get_endpoint_access_validation_data",
            new_callable=AsyncMock,
        )

    @pytest.mark.parametrize(
        "scenario",
        [
            ScenarioBase.success(
                "get model service info",
                GetModelServiceInfoAction(
                    service_id=uuid.UUID("33333333-4444-5555-6666-777777777777"),
                ),
                GetModelServiceInfoActionResult(
                    data=ServiceInfo(
                        endpoint_id=uuid.UUID("33333333-4444-5555-6666-777777777777"),
                        model_id=uuid.UUID("11111111-1111-1111-1111-111111111111"),
                        extra_mounts=[],
                        name="test-model-v1.0",
                        model_definition_path=None,
                        replicas=3,
                        desired_session_count=3,
                        active_routes=[],
                        service_endpoint=HttpUrl(
                            "https://api.example.com/v1/models/test-model/v1.0"
                        ),
                        is_public=False,
                        runtime_variant=RuntimeVariant.CUSTOM,
                    ),
                ),
            ),
        ],
    )
    @pytest.mark.asyncio
    async def test_get_model_service_info(
        self,
        scenario: ScenarioBase[GetModelServiceInfoAction, GetModelServiceInfoActionResult],
        user_data: UserData,
        model_serving_processors: ModelServingProcessors,
        mock_check_user_access_get_info: AsyncMock,
        mock_get_endpoint_by_id_get_info: AsyncMock,
        mock_get_endpoint_access_validation_data_get_info: AsyncMock,
    ) -> None:
        # Mock repository responses
        expected = cast(GetModelServiceInfoActionResult, scenario.expected)

        mock_validation_data = MagicMock(
            session_owner_id=user_data.user_id,
            session_owner_role=UserRole(user_data.role),
            domain=user_data.domain_name,
        )
        mock_get_endpoint_access_validation_data_get_info.return_value = mock_validation_data

        mock_endpoint = MagicMock(
            id=expected.data.endpoint_id,
            model=expected.data.model_id,
            extra_mounts=[
                MagicMock(vfid=MagicMock(folder_id=mount_id))
                for mount_id in expected.data.extra_mounts
            ],
            model_definition_path=expected.data.model_definition_path,
            replicas=expected.data.replicas,
            routings=[
                MagicMock(
                    id=route.route_id,
                    session=route.session_id,
                    traffic_ratio=route.traffic_ratio,
                )
                for route in expected.data.active_routes
            ]
            if expected.data.active_routes
            else [],
            url=str(expected.data.service_endpoint) if expected.data.service_endpoint else None,
            open_to_public=expected.data.is_public,
            runtime_variant=expected.data.runtime_variant,
        )
        mock_endpoint.name = expected.data.name

        # Now uses single repository for all roles
        mock_get_endpoint_by_id_get_info.return_value = mock_endpoint

        async def get_model_service_info(action: GetModelServiceInfoAction) -> GetModelServiceInfoActionResult:
            return await model_serving_processors.get_model_service_info.wait_for_complete(action)

        await scenario.test(get_model_service_info)
