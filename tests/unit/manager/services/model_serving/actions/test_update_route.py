from __future__ import annotations

import uuid
from collections.abc import Iterator
from typing import Any, cast
from unittest.mock import AsyncMock, MagicMock

import aiohttp
import pytest

from ai.backend.common.bgtask.bgtask import BackgroundTaskManager
from ai.backend.common.contexts.user import with_user
from ai.backend.common.data.user.types import UserData, UserRole
from ai.backend.common.events.dispatcher import EventDispatcher
from ai.backend.common.events.hub import EventHub
from ai.backend.manager.actions.monitors.monitor import ActionMonitor
from ai.backend.manager.clients.storage_proxy.session_manager import StorageSessionManager
from ai.backend.manager.config.provider import ManagerConfigProvider
from ai.backend.manager.errors.service import ModelServiceNotFound
from ai.backend.manager.repositories.model_serving.repositories import ModelServingRepositories
from ai.backend.manager.repositories.model_serving.repository import ModelServingRepository
from ai.backend.manager.services.model_serving.actions.update_route import (
    UpdateRouteAction,
    UpdateRouteActionResult,
)
from ai.backend.manager.services.model_serving.processors.model_serving import (
    ModelServingProcessors,
)
from ai.backend.manager.services.model_serving.services.model_serving import ModelServingService
from ai.backend.manager.sokovan.deployment.deployment_controller import DeploymentController
from ai.backend.manager.sokovan.scheduling_controller import SchedulingController
from ai.backend.testutils.scenario import ScenarioBase


class TestUpdateRoute:
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
    def mock_check_user_access_update_route(
        self, mocker: Any, model_serving_service: Any
    ) -> AsyncMock:
        mock = cast(
            AsyncMock,
            mocker.patch.object(
                model_serving_service,
                "check_user_access",
                new_callable=AsyncMock,
            ),
        )
        mock.return_value = None
        return mock

    @pytest.fixture
    def mock_get_endpoint_access_validation_data_update_route(
        self, mocker: Any, mock_repositories: Any
    ) -> AsyncMock:
        return cast(
            AsyncMock,
            mocker.patch.object(
                mock_repositories.repository,
                "get_endpoint_access_validation_data",
                new_callable=AsyncMock,
            ),
        )

    @pytest.fixture
    def mock_update_route_traffic(self, mocker: Any, mock_repositories: Any) -> AsyncMock:
        return cast(
            AsyncMock,
            mocker.patch.object(
                mock_repositories.repository,
                "update_route_traffic",
                new_callable=AsyncMock,
            ),
        )

    @pytest.fixture
    def mock_get_endpoint_for_appproxy_update(
        self, mocker: Any, mock_repositories: Any
    ) -> AsyncMock:
        return cast(
            AsyncMock,
            mocker.patch.object(
                mock_repositories.repository,
                "get_endpoint_for_appproxy_update",
                new_callable=AsyncMock,
            ),
        )

    @pytest.fixture
    def mock_notify_endpoint_route_update_to_appproxy(
        self, mocker: Any, mock_agent_registry: Any
    ) -> AsyncMock:
        mock = cast(
            AsyncMock,
            mocker.patch.object(
                mock_agent_registry,
                "notify_endpoint_route_update_to_appproxy",
                new_callable=AsyncMock,
            ),
        )
        mock.return_value = None
        return mock

    @pytest.mark.parametrize(
        "scenario",
        [
            ScenarioBase.success(
                "update route traffic ratio",
                UpdateRouteAction(
                    service_id=uuid.UUID("55555555-6666-7777-8888-999999999999"),
                    route_id=uuid.UUID("11111111-1111-1111-1111-111111111111"),
                    traffic_ratio=0.7,
                ),
                UpdateRouteActionResult(success=True),
            ),
        ],
    )
    @pytest.mark.asyncio
    async def test_update_route(
        self,
        scenario: ScenarioBase[UpdateRouteAction, UpdateRouteActionResult],
        user_data: UserData,
        model_serving_processors: ModelServingProcessors,
        mock_check_user_access_update_route: AsyncMock,
        mock_get_endpoint_access_validation_data_update_route: AsyncMock,
        mock_update_route_traffic: AsyncMock,
        mock_get_endpoint_for_appproxy_update: AsyncMock,
        mock_notify_endpoint_route_update_to_appproxy: AsyncMock,
    ) -> None:
        action = scenario.input

        # Mock validation data for access validation
        mock_validation_data = MagicMock(
            session_owner_id=user_data.user_id,
            session_owner_role=UserRole(user_data.role),
            domain=user_data.domain_name,
        )

        # Mock route data
        mock_route_data = MagicMock(
            id=action.service_id,
            route_id=action.route_id,
            traffic_ratio=action.traffic_ratio,
        )

        # Mock endpoint row for AppProxy update
        mock_endpoint_row = MagicMock(
            id=action.service_id,
            url="https://api.example.com/v1/models/test-model",
            routings=[
                MagicMock(
                    id=action.route_id,
                    traffic_ratio=action.traffic_ratio,
                    session=uuid.UUID("aaaaaaaa-bbbb-cccc-dddd-eeeeeeeeeeee"),
                )
            ],
        )

        # Setup mocks - now uses single repository for all roles
        mock_get_endpoint_access_validation_data_update_route.return_value = mock_validation_data
        mock_update_route_traffic.return_value = mock_route_data
        mock_get_endpoint_for_appproxy_update.return_value = mock_endpoint_row

        async def update_route(action: UpdateRouteAction) -> UpdateRouteActionResult:
            return await model_serving_processors.update_route.wait_for_complete(action)

        await scenario.test(update_route)

    @pytest.mark.parametrize(
        "scenario",
        [
            ScenarioBase.failure(
                "non-existent route",
                UpdateRouteAction(
                    service_id=uuid.UUID("55555555-6666-7777-8888-999999999999"),
                    route_id=uuid.UUID("99999999-9999-9999-9999-999999999999"),
                    traffic_ratio=0.5,
                ),
                ModelServiceNotFound,
            ),
        ],
    )
    @pytest.mark.asyncio
    async def test_update_route_failure(
        self,
        scenario: ScenarioBase[UpdateRouteAction, Exception],
        user_data: UserData,
        model_serving_processors: ModelServingProcessors,
        mock_check_user_access_update_route: AsyncMock,
        mock_get_endpoint_access_validation_data_update_route: AsyncMock,
        mock_update_route_traffic: AsyncMock,
    ) -> None:
        # Mock validation data for access validation
        mock_validation_data = MagicMock(
            session_owner_id=user_data.user_id,
            session_owner_role=UserRole(user_data.role),
            domain=user_data.domain_name,
        )
        mock_get_endpoint_access_validation_data_update_route.return_value = mock_validation_data

        # Mock repository to return None (route not found)
        mock_update_route_traffic.return_value = None

        async def update_route(action: UpdateRouteAction) -> None:
            await model_serving_processors.update_route.wait_for_complete(action)

        await scenario.test(update_route)

    @pytest.mark.asyncio
    async def test_update_route_appproxy_failure(
        self,
        user_data: UserData,
        model_serving_processors: ModelServingProcessors,
        mock_check_user_access_update_route: AsyncMock,
        mock_get_endpoint_access_validation_data_update_route: AsyncMock,
        mock_update_route_traffic: AsyncMock,
        mock_get_endpoint_for_appproxy_update: AsyncMock,
        mock_notify_endpoint_route_update_to_appproxy: AsyncMock,
    ) -> None:
        action = UpdateRouteAction(
            service_id=uuid.UUID("55555555-6666-7777-8888-999999999999"),
            route_id=uuid.UUID("11111111-1111-1111-1111-111111111111"),
            traffic_ratio=0.7,
        )

        # Mock validation data for access validation
        mock_validation_data = MagicMock(
            session_owner_id=user_data.user_id,
            session_owner_role=UserRole(user_data.role),
            domain=user_data.domain_name,
        )
        mock_get_endpoint_access_validation_data_update_route.return_value = mock_validation_data

        # Mock successful route update
        mock_update_route_traffic.return_value = MagicMock(id=action.service_id)
        mock_get_endpoint_for_appproxy_update.return_value = MagicMock(id=action.service_id)

        # Mock AppProxy communication failure
        mock_notify_endpoint_route_update_to_appproxy.side_effect = aiohttp.ClientError(
            "Connection failed"
        )

        # AppProxy failure should propagate as exception
        with pytest.raises(aiohttp.ClientError, match="Connection failed"):
            await model_serving_processors.update_route.wait_for_complete(action)
