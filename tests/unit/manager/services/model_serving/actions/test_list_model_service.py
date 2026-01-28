from __future__ import annotations

import uuid
from collections.abc import Iterator
from typing import cast
from unittest.mock import AsyncMock, MagicMock

import pytest
from pydantic import HttpUrl

from ai.backend.common.bgtask.bgtask import BackgroundTaskManager
from ai.backend.common.contexts.user import with_user
from ai.backend.common.data.user.types import UserData, UserRole
from ai.backend.common.events.dispatcher import EventDispatcher
from ai.backend.common.events.hub import EventHub
from ai.backend.manager.actions.monitors.monitor import ActionMonitor
from ai.backend.manager.clients.storage_proxy.session_manager import StorageSessionManager
from ai.backend.manager.config.provider import ManagerConfigProvider
from ai.backend.manager.data.model_serving.types import CompactServiceInfo
from ai.backend.manager.models.routing import RouteStatus
from ai.backend.manager.repositories.model_serving.repositories import ModelServingRepositories
from ai.backend.manager.repositories.model_serving.repository import ModelServingRepository
from ai.backend.manager.services.model_serving.actions.list_model_service import (
    ListModelServiceAction,
    ListModelServiceActionResult,
)
from ai.backend.manager.services.model_serving.processors.model_serving import (
    ModelServingProcessors,
)
from ai.backend.manager.services.model_serving.services.model_serving import ModelServingService
from ai.backend.manager.sokovan.deployment.deployment_controller import DeploymentController
from ai.backend.manager.sokovan.scheduling_controller import SchedulingController
from ai.backend.testutils.scenario import ScenarioBase


class TestListModelService:
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
    def mock_list_endpoints_by_owner_validated(self, mocker, mock_repositories) -> AsyncMock:
        return mocker.patch.object(
            mock_repositories.repository,
            "list_endpoints_by_owner_validated",
            new_callable=AsyncMock,
        )

    @pytest.mark.parametrize(
        "scenario",
        [
            ScenarioBase.success(
                "all model service list",
                ListModelServiceAction(
                    session_owener_id=uuid.UUID("00000000-0000-0000-0000-000000000001"),
                    name=None,
                ),
                ListModelServiceActionResult(
                    data=[
                        CompactServiceInfo(
                            id=uuid.UUID("88888888-9999-aaaa-bbbb-cccccccccccc"),
                            name="model-1-v1.0",
                            replicas=2,
                            desired_session_count=2,
                            active_route_count=2,
                            service_endpoint=HttpUrl(
                                "https://api.example.com/v1/models/model-1/v1.0"
                            ),
                            is_public=False,
                        ),
                        CompactServiceInfo(
                            id=uuid.UUID("99999999-aaaa-bbbb-cccc-dddddddddddd"),
                            name="model-2-v2.0",
                            replicas=3,
                            desired_session_count=3,
                            active_route_count=3,
                            service_endpoint=HttpUrl(
                                "https://api.example.com/v1/models/model-2/v2.0"
                            ),
                            is_public=False,
                        ),
                    ]
                ),
            ),
            ScenarioBase.success(
                "name filtered",
                ListModelServiceAction(
                    session_owener_id=uuid.UUID("00000000-0000-0000-0000-000000000001"),
                    name="project-model",
                ),
                ListModelServiceActionResult(
                    data=[
                        CompactServiceInfo(
                            id=uuid.UUID("bbbbbbbb-cccc-dddd-eeee-ffffffffffff"),
                            name="project-model",
                            replicas=1,
                            desired_session_count=1,
                            active_route_count=1,
                            service_endpoint=HttpUrl(
                                "https://api.example.com/v1/models/project-model/v1.0"
                            ),
                            is_public=False,
                        ),
                    ]
                ),
            ),
        ],
    )
    @pytest.mark.asyncio
    async def test_list_model_service(
        self,
        scenario: ScenarioBase[ListModelServiceAction, ListModelServiceActionResult],
        model_serving_processors: ModelServingProcessors,
        mock_list_endpoints_by_owner_validated,
    ):
        # Mock repository responses
        mock_endpoints = []
        expected = cast(ListModelServiceActionResult, scenario.expected)
        for endpoint_data in expected.data:
            mock_endpoint = MagicMock(
                id=endpoint_data.id,
                replicas=endpoint_data.replicas,
                desired_session_count=endpoint_data.replicas,
                routings=[
                    MagicMock(status=RouteStatus.HEALTHY)
                    for _ in range(endpoint_data.active_route_count)
                ],
                url=str(endpoint_data.service_endpoint),
                open_to_public=endpoint_data.is_public,
            )
            mock_endpoint.name = (
                endpoint_data.name
            )  # As 'name' is special attribute in MagicMock, we set it this way
            mock_endpoints.append(mock_endpoint)

        mock_list_endpoints_by_owner_validated.return_value = mock_endpoints

        async def list_model_service(action: ListModelServiceAction):
            return await model_serving_processors.list_model_service.wait_for_complete(action)

        await scenario.test(list_model_service)
