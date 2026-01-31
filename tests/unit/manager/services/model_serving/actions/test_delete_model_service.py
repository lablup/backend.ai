from __future__ import annotations
from typing import Any

import uuid
from collections.abc import Iterator
from unittest.mock import AsyncMock, MagicMock

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
from typing import cast

from ai.backend.manager.services.model_serving.actions.delete_model_service import (
    DeleteModelServiceAction,
    DeleteModelServiceActionResult,
)
from ai.backend.manager.services.model_serving.processors.model_serving import (
    ModelServingProcessors,
)
from ai.backend.manager.services.model_serving.services.model_serving import ModelServingService
from ai.backend.manager.sokovan.deployment.deployment_controller import DeploymentController
from ai.backend.manager.sokovan.scheduling_controller import SchedulingController
from ai.backend.testutils.scenario import ScenarioBase


class TestDeleteModelService:
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
    def mock_get_endpoint_by_id(self, mocker: Any, mock_repositories: Any)-> AsyncMock:
        return cast(
        AsyncMock,
        mocker.patch.object(
            mock_repositories.repository,
            "get_endpoint_by_id",
            new_callable=AsyncMock,
        ),
    )

    @pytest.fixture
    def mock_get_endpoint_access_validation_data(self, mocker: Any, mock_repositories: Any)-> AsyncMock:
        return cast(
        AsyncMock,
        mocker.patch.object(
            mock_repositories.repository,
            "get_endpoint_access_validation_data",
            new_callable=AsyncMock,
        ),
    )

    @pytest.fixture
    def mock_update_endpoint_lifecycle(self, mocker: Any, mock_repositories: Any)-> AsyncMock:
        return cast(
        AsyncMock,
        mocker.patch.object(
            mock_repositories.repository,
            "update_endpoint_lifecycle",
            new_callable=AsyncMock,
        ),
    )

    @pytest.fixture
    def mock_check_user_access(self, mocker: Any, model_serving_service: Any)-> AsyncMock:
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

    @pytest.mark.parametrize(
        "scenario",
        [
            ScenarioBase.success(
                "successful model deletion",
                DeleteModelServiceAction(
                    service_id=uuid.UUID("cccccccc-dddd-eeee-ffff-111111111111"),
                ),
                DeleteModelServiceActionResult(
                    success=True,
                ),
            ),
            ScenarioBase.failure(
                "non-existent model",
                DeleteModelServiceAction(
                    service_id=uuid.UUID("dddddddd-eeee-ffff-1111-222222222222"),
                ),
                ModelServiceNotFound,
            ),
        ],
    )
    @pytest.mark.asyncio
    async def test_delete_model_service(
        self,
        scenario: ScenarioBase[DeleteModelServiceAction, DeleteModelServiceActionResult],
        user_data: UserData,
        model_serving_processors: ModelServingProcessors,
        mock_get_endpoint_by_id: AsyncMock,
        mock_get_endpoint_access_validation_data: AsyncMock,
        mock_update_endpoint_lifecycle: AsyncMock,
        mock_check_user_access: AsyncMock,
    ) -> None:
        mock_validation_data = MagicMock(
            session_owner_id=user_data.user_id,
            session_owner_role=UserRole(user_data.role),
            domain=user_data.domain_name,
        )
        mock_endpoint = MagicMock(
            routings=[],
        )

        # Mock repository responses based on scenario
        if "successful" in scenario.description:
            mock_get_endpoint_access_validation_data.return_value = mock_validation_data
            mock_get_endpoint_by_id.return_value = mock_endpoint
            mock_update_endpoint_lifecycle.return_value = None
        else:  # non-existent model
            mock_get_endpoint_access_validation_data.return_value = None
            mock_get_endpoint_by_id.return_value = None

        async def delete_model_service(action: DeleteModelServiceAction) -> DeleteModelServiceActionResult:
            return await model_serving_processors.delete_model_service.wait_for_complete(action)

        await scenario.test(delete_model_service)
