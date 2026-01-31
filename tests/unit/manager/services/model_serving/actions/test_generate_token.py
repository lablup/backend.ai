from __future__ import annotations

import uuid
from collections.abc import Iterator
from datetime import UTC, datetime
from typing import cast, Any
from unittest.mock import AsyncMock, MagicMock, patch

import pytest
from aioresponses import aioresponses

from ai.backend.common.bgtask.bgtask import BackgroundTaskManager
from ai.backend.common.contexts.user import with_user
from ai.backend.common.data.endpoint.types import EndpointStatus
from ai.backend.common.data.user.types import UserData, UserRole
from ai.backend.common.events.dispatcher import EventDispatcher
from ai.backend.common.events.hub import EventHub
from ai.backend.manager.actions.monitors.monitor import ActionMonitor
from ai.backend.manager.clients.storage_proxy.session_manager import StorageSessionManager
from ai.backend.manager.config.provider import ManagerConfigProvider
from ai.backend.manager.data.model_serving.types import EndpointTokenData
from ai.backend.manager.repositories.model_serving.repositories import ModelServingRepositories
from ai.backend.manager.repositories.model_serving.repository import ModelServingRepository
from ai.backend.manager.services.model_serving.actions.generate_token import (
    GenerateTokenAction,
    GenerateTokenActionResult,
)
from ai.backend.manager.services.model_serving.processors.model_serving import (
    ModelServingProcessors,
)
from ai.backend.manager.services.model_serving.services.model_serving import ModelServingService
from ai.backend.manager.sokovan.deployment.deployment_controller import DeploymentController
from ai.backend.manager.sokovan.scheduling_controller import SchedulingController
from ai.backend.testutils.scenario import ScenarioBase


class TestGenerateToken:
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
    def mock_check_user_access_token(self, mocker: Any, model_serving_service: Any)-> AsyncMock:
        mock = mocker.patch.object(
            model_serving_service,
            "check_user_access",
            new_callable=AsyncMock,
        )
        mock.return_value = None
        return mock

    @pytest.fixture
    def mock_get_endpoint_by_id_token(self, mocker: Any, mock_repositories: Any)-> AsyncMock:
        return mocker.patch.object(
            mock_repositories.repository,
            "get_endpoint_by_id",
            new_callable=AsyncMock,
        )

    @pytest.fixture
    def mock_get_endpoint_access_validation_data_token(
        self, mocker: Any, mock_repositories: Any
    ) -> AsyncMock:
        return mocker.patch.object(
            mock_repositories.repository,
            "get_endpoint_access_validation_data",
            new_callable=AsyncMock,
        )

    @pytest.fixture
    def mock_create_endpoint_token(self, mocker: Any, mock_repositories: Any)-> AsyncMock:
        return mocker.patch.object(
            mock_repositories.repository,
            "create_endpoint_token",
            new_callable=AsyncMock,
        )

    @pytest.fixture
    def mock_get_scaling_group_info_token(self, mocker: Any, mock_repositories: Any)-> AsyncMock:
        return mocker.patch.object(
            mock_repositories.repository,
            "get_scaling_group_info",
            new_callable=AsyncMock,
        )

    @pytest.mark.parametrize(
        "scenario",
        [
            ScenarioBase.success(
                "regular token generation",
                GenerateTokenAction(
                    service_id=uuid.UUID("dddddddd-dddd-dddd-dddd-dddddddddddd"),
                    duration=None,
                    valid_until=None,
                    expires_at=int(datetime.now(tz=UTC).timestamp()) + 86400,
                ),
                GenerateTokenActionResult(
                    data=EndpointTokenData(
                        id=uuid.UUID("12345678-1234-1234-1234-123456789012"),
                        token="jwt_token_example",
                        endpoint=uuid.UUID("dddddddd-dddd-dddd-dddd-dddddddddddd"),
                        session_owner=uuid.UUID("00000000-0000-0000-0000-000000000001"),
                        domain="default",
                        project=uuid.UUID("00000000-0000-0000-0000-000000000002"),
                        created_at=datetime.now(tz=UTC),
                    ),
                ),
            ),
            ScenarioBase.success(
                "unlimited token",
                GenerateTokenAction(
                    service_id=uuid.UUID("eeeeeeee-eeee-eeee-eeee-eeeeeeeeeeee"),
                    duration=None,
                    valid_until=None,
                    expires_at=0,  # No expiry
                ),
                GenerateTokenActionResult(
                    data=EndpointTokenData(
                        id=uuid.UUID("12345678-1234-1234-1234-123456789013"),
                        token="jwt_token_unlimited",
                        endpoint=uuid.UUID("eeeeeeee-eeee-eeee-eeee-eeeeeeeeeeee"),
                        session_owner=uuid.UUID("00000000-0000-0000-0000-000000000001"),
                        domain="default",
                        project=uuid.UUID("00000000-0000-0000-0000-000000000002"),
                        created_at=datetime.now(tz=UTC),
                    ),
                ),
            ),
            ScenarioBase.success(
                "limited scope token",
                GenerateTokenAction(
                    service_id=uuid.UUID("ffffffff-ffff-ffff-ffff-ffffffffffff"),
                    duration=None,
                    valid_until=None,
                    expires_at=int(datetime.now(tz=UTC).timestamp()) + 3600,
                ),
                GenerateTokenActionResult(
                    data=EndpointTokenData(
                        id=uuid.UUID("12345678-1234-1234-1234-123456789014"),
                        token="jwt_token_restricted",
                        endpoint=uuid.UUID("ffffffff-ffff-ffff-ffff-ffffffffffff"),
                        session_owner=uuid.UUID("00000000-0000-0000-0000-000000000001"),
                        domain="default",
                        project=uuid.UUID("00000000-0000-0000-0000-000000000002"),
                        created_at=datetime.now(tz=UTC),
                    ),
                ),
            ),
        ],
    )
    @pytest.mark.asyncio
    async def test_generate_token(
        self,
        scenario: ScenarioBase[GenerateTokenAction, GenerateTokenActionResult],
        user_data: UserData,
        model_serving_processors: ModelServingProcessors,
        mock_check_user_access_token: AsyncMock,
        mock_get_endpoint_by_id_token: AsyncMock,
        mock_get_endpoint_access_validation_data_token: AsyncMock,
        mock_create_endpoint_token: AsyncMock,
        mock_get_scaling_group_info_token: AsyncMock,
    ) -> None:
        action = scenario.input
        expected = scenario.expected

        # Mock setup based on scenario data
        expected = cast(GenerateTokenActionResult, expected)

        mock_validation_data = MagicMock(
            session_owner_id=expected.data.session_owner,
            session_owner_role=UserRole(user_data.role),
            domain=expected.data.domain,
        )
        mock_get_endpoint_access_validation_data_token.return_value = mock_validation_data

        mock_endpoint = MagicMock(
            id=action.service_id,
            status=EndpointStatus.READY,
            session_owner_id=expected.data.session_owner,
            domain=expected.data.domain,
            project=expected.data.project,
            resource_group="default",
        )

        mock_scaling_group = MagicMock(
            wsproxy_addr="http://test-wsproxy:8080", wsproxy_api_token="test-api-token"
        )

        mock_token_data = MagicMock(
            id=expected.data.id,
            token=expected.data.token,
            endpoint=expected.data.endpoint,
            session_owner=expected.data.session_owner,
            domain=expected.data.domain,
            project=expected.data.project,
            created_at=expected.data.created_at,
        )

        # Setup repository mocks - now uses single repository for all roles
        mock_get_endpoint_by_id_token.return_value = mock_endpoint
        mock_create_endpoint_token.return_value = mock_token_data
        mock_get_scaling_group_info_token.return_value = mock_scaling_group

        # TODO: Change using aioresponses to mocking client layer after refactoring service layer
        with aioresponses() as mock_http:
            # HTTP response mock setup
            expected_url = (
                f"{mock_scaling_group.wsproxy_addr}/v2/endpoints/{action.service_id}/token"
            )
            mock_http.post(expected_url, payload={"token": expected.data.token}, status=200)

            with patch("uuid.uuid4", return_value=expected.data.id):

                async def generate_token(action: GenerateTokenAction) -> GenerateTokenActionResult:
                    return await model_serving_processors.generate_token.wait_for_complete(action)

                await scenario.test(generate_token)
