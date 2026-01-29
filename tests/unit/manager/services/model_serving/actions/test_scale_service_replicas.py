import uuid
from collections.abc import Iterator
from typing import cast
from unittest.mock import AsyncMock, MagicMock

import pytest

from ai.backend.common.contexts.user import with_user
from ai.backend.common.data.user.types import UserData, UserRole
from ai.backend.manager.actions.monitors.monitor import ActionMonitor
from ai.backend.manager.repositories.model_serving.repositories import ModelServingRepositories
from ai.backend.manager.repositories.model_serving.repository import ModelServingRepository
from ai.backend.manager.services.model_serving.actions.scale_service_replicas import (
    ScaleServiceReplicasAction,
    ScaleServiceReplicasActionResult,
)
from ai.backend.manager.services.model_serving.exceptions import (
    ModelServiceNotFound,
)
from ai.backend.manager.services.model_serving.processors.auto_scaling import (
    ModelServingAutoScalingProcessors,
)
from ai.backend.manager.services.model_serving.services.auto_scaling import AutoScalingService
from ai.backend.testutils.scenario import ScenarioBase


class TestScaleServiceReplicas:
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
    def mock_action_monitor(self) -> MagicMock:
        return MagicMock(spec=ActionMonitor)

    @pytest.fixture
    def mock_repositories(self) -> MagicMock:
        mock = MagicMock(spec=ModelServingRepositories)
        mock.repository = MagicMock(spec=ModelServingRepository)
        return mock

    @pytest.fixture
    def auto_scaling_service(
        self,
        mock_repositories: MagicMock,
    ) -> AutoScalingService:
        return AutoScalingService(
            repository=mock_repositories.repository,
        )

    @pytest.fixture
    def auto_scaling_processors(
        self,
        mock_action_monitor: MagicMock,
        auto_scaling_service: AutoScalingService,
    ) -> ModelServingAutoScalingProcessors:
        return ModelServingAutoScalingProcessors(
            service=auto_scaling_service,
            action_monitors=[mock_action_monitor],
        )

    @pytest.fixture
    def mock_check_user_access_scale(self, mocker, auto_scaling_service) -> AsyncMock:
        mock = mocker.patch.object(
            auto_scaling_service,
            "check_user_access",
            new_callable=AsyncMock,
        )
        mock.return_value = None
        return mock

    @pytest.fixture
    def mock_get_endpoint_by_id_scale(self, mocker, mock_repositories) -> AsyncMock:
        return mocker.patch.object(
            mock_repositories.repository,
            "get_endpoint_by_id",
            new_callable=AsyncMock,
        )

    @pytest.fixture
    def mock_get_endpoint_access_validation_data_scale(
        self, mocker, mock_repositories
    ) -> AsyncMock:
        return mocker.patch.object(
            mock_repositories.repository,
            "get_endpoint_access_validation_data",
            new_callable=AsyncMock,
        )

    @pytest.fixture
    def mock_update_endpoint_replicas(self, mocker, mock_repositories) -> AsyncMock:
        return mocker.patch.object(
            mock_repositories.repository,
            "update_endpoint_replicas",
            new_callable=AsyncMock,
        )

    @pytest.mark.parametrize(
        "scenario",
        [
            ScenarioBase.success(
                "scale up",
                ScaleServiceReplicasAction(
                    max_session_count_per_model_session=100,
                    service_id=uuid.UUID("99999999-9999-9999-9999-999999999999"),
                    to=5,
                ),
                ScaleServiceReplicasActionResult(
                    current_route_count=2,
                    target_count=5,
                ),
            ),
            ScenarioBase.success(
                "scale down",
                ScaleServiceReplicasAction(
                    max_session_count_per_model_session=100,
                    service_id=uuid.UUID("aaaaaaaa-aaaa-aaaa-aaaa-aaaaaaaaaaaa"),
                    to=1,
                ),
                ScaleServiceReplicasActionResult(
                    current_route_count=5,
                    target_count=1,
                ),
            ),
            ScenarioBase.success(
                "zero scale",
                ScaleServiceReplicasAction(
                    max_session_count_per_model_session=100,
                    service_id=uuid.UUID("bbbbbbbb-bbbb-bbbb-bbbb-bbbbbbbbbbbb"),
                    to=0,
                ),
                ScaleServiceReplicasActionResult(
                    current_route_count=2,
                    target_count=0,
                ),
            ),
            ScenarioBase.failure(
                "non-existent service",
                ScaleServiceReplicasAction(
                    max_session_count_per_model_session=100,
                    service_id=uuid.UUID("cccccccc-cccc-cccc-cccc-cccccccccccc"),
                    to=5,
                ),
                ModelServiceNotFound,
            ),
            ScenarioBase.failure(
                "update operation failed",
                ScaleServiceReplicasAction(
                    max_session_count_per_model_session=100,
                    service_id=uuid.UUID("eeeeeeee-eeee-eeee-eeee-eeeeeeeeeeee"),
                    to=3,
                ),
                ModelServiceNotFound,
            ),
        ],
    )
    @pytest.mark.asyncio
    async def test_scale_service_replicas(
        self,
        scenario: ScenarioBase[ScaleServiceReplicasAction, ScaleServiceReplicasActionResult],
        user_data: UserData,
        auto_scaling_processors: ModelServingAutoScalingProcessors,
        mock_check_user_access_scale,
        mock_get_endpoint_by_id_scale,
        mock_get_endpoint_access_validation_data_scale,
        mock_update_endpoint_replicas,
    ) -> None:
        expected = cast(ScaleServiceReplicasActionResult, scenario.expected)
        action = scenario.input

        # Mock endpoint data based on scenario
        if scenario.description in ["scale up", "scale down", "zero scale"]:
            mock_validation_data = MagicMock(
                session_owner_id=user_data.user_id,
                session_owner_role=UserRole(user_data.role),
                domain=user_data.domain_name,
            )
            mock_get_endpoint_access_validation_data_scale.return_value = mock_validation_data
            mock_endpoint = MagicMock(
                id=action.service_id,
                routings=[MagicMock() for _ in range(expected.current_route_count)],
            )
            mock_get_endpoint_by_id_scale.return_value = mock_endpoint
            mock_update_endpoint_replicas.return_value = True

        elif scenario.description == "non-existent service":
            mock_get_endpoint_access_validation_data_scale.return_value = None
            mock_get_endpoint_by_id_scale.return_value = None

        elif scenario.description == "update operation failed":
            mock_validation_data = MagicMock(
                session_owner_id=user_data.user_id,
                session_owner_role=UserRole(user_data.role),
                domain=user_data.domain_name,
            )
            mock_get_endpoint_access_validation_data_scale.return_value = mock_validation_data
            mock_endpoint = MagicMock(
                id=action.service_id,
                routings=[MagicMock() for _ in range(2)],
            )
            mock_get_endpoint_by_id_scale.return_value = mock_endpoint
            mock_update_endpoint_replicas.return_value = False

        async def scale_service_replicas(action: ScaleServiceReplicasAction):
            return await auto_scaling_processors.scale_service_replicas.wait_for_complete(action)

        await scenario.test(scale_service_replicas)
