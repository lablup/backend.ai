import uuid
from typing import cast
from unittest.mock import AsyncMock, MagicMock

import pytest

from ai.backend.manager.data.model_serving.types import RequesterCtx
from ai.backend.manager.models.user import UserRole
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

from ...utils import ScenarioBase


@pytest.fixture
def mock_check_requester_access_scale(mocker, auto_scaling_service):
    mock = mocker.patch.object(
        auto_scaling_service,
        "check_requester_access",
        new_callable=AsyncMock,
    )
    mock.return_value = None
    return mock


@pytest.fixture
def mock_get_endpoint_by_id_force_scale(mocker, mock_repositories):
    mock = mocker.patch.object(
        mock_repositories.admin_repository,
        "get_endpoint_by_id_force",
        new_callable=AsyncMock,
    )
    return mock


@pytest.fixture
def mock_update_endpoint_replicas_force(mocker, mock_repositories):
    mock = mocker.patch.object(
        mock_repositories.admin_repository,
        "update_endpoint_replicas_force",
        new_callable=AsyncMock,
    )
    return mock


@pytest.fixture
def mock_get_endpoint_by_id_validated_scale(mocker, mock_repositories):
    mock = mocker.patch.object(
        mock_repositories.repository,
        "get_endpoint_by_id_validated",
        new_callable=AsyncMock,
    )
    return mock


@pytest.fixture
def mock_update_endpoint_replicas_validated(mocker, mock_repositories):
    mock = mocker.patch.object(
        mock_repositories.repository,
        "update_endpoint_replicas_validated",
        new_callable=AsyncMock,
    )
    return mock


class TestScaleServiceReplicas:
    @pytest.mark.parametrize(
        "scenario",
        [
            ScenarioBase.success(
                "scale up",
                ScaleServiceReplicasAction(
                    requester_ctx=RequesterCtx(
                        is_authorized=True,
                        user_id=uuid.UUID("00000000-0000-0000-0000-000000000001"),
                        user_role=UserRole.USER,
                        domain_name="default",
                    ),
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
                    requester_ctx=RequesterCtx(
                        is_authorized=True,
                        user_id=uuid.UUID("00000000-0000-0000-0000-000000000001"),
                        user_role=UserRole.USER,
                        domain_name="default",
                    ),
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
                    requester_ctx=RequesterCtx(
                        is_authorized=True,
                        user_id=uuid.UUID("00000000-0000-0000-0000-000000000001"),
                        user_role=UserRole.USER,
                        domain_name="default",
                    ),
                    max_session_count_per_model_session=100,
                    service_id=uuid.UUID("bbbbbbbb-bbbb-bbbb-bbbb-bbbbbbbbbbbb"),
                    to=0,
                ),
                ScaleServiceReplicasActionResult(
                    current_route_count=2,
                    target_count=0,
                ),
            ),
            ScenarioBase.success(
                "SUPERADMIN scale up",
                ScaleServiceReplicasAction(
                    requester_ctx=RequesterCtx(
                        is_authorized=True,
                        user_id=uuid.UUID("00000000-0000-0000-0000-000000000001"),
                        user_role=UserRole.SUPERADMIN,
                        domain_name="default",
                    ),
                    max_session_count_per_model_session=100,
                    service_id=uuid.UUID("dddddddd-dddd-dddd-dddd-dddddddddddd"),
                    to=10,
                ),
                ScaleServiceReplicasActionResult(
                    current_route_count=3,
                    target_count=10,
                ),
            ),
            ScenarioBase.failure(
                "non-existent service",
                ScaleServiceReplicasAction(
                    requester_ctx=RequesterCtx(
                        is_authorized=True,
                        user_id=uuid.UUID("00000000-0000-0000-0000-000000000001"),
                        user_role=UserRole.USER,
                        domain_name="default",
                    ),
                    max_session_count_per_model_session=100,
                    service_id=uuid.UUID("cccccccc-cccc-cccc-cccc-cccccccccccc"),
                    to=5,
                ),
                ModelServiceNotFound,
            ),
            ScenarioBase.failure(
                "update operation failed",
                ScaleServiceReplicasAction(
                    requester_ctx=RequesterCtx(
                        is_authorized=True,
                        user_id=uuid.UUID("00000000-0000-0000-0000-000000000001"),
                        user_role=UserRole.USER,
                        domain_name="default",
                    ),
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
        auto_scaling_processors: ModelServingAutoScalingProcessors,
        mock_check_requester_access_scale,
        mock_get_endpoint_by_id_force_scale,
        mock_update_endpoint_replicas_force,
        mock_get_endpoint_by_id_validated_scale,
        mock_update_endpoint_replicas_validated,
    ):
        expected = cast(ScaleServiceReplicasActionResult, scenario.expected)

        # Mock endpoint data based on scenario
        if scenario.description in ["scale up", "scale down", "zero scale"]:
            mock_endpoint = MagicMock(
                id=scenario.input.service_id,
                routings=[MagicMock() for _ in range(expected.current_route_count)],
            )
            mock_get_endpoint_by_id_validated_scale.return_value = mock_endpoint
            mock_update_endpoint_replicas_validated.return_value = True

        elif scenario.description == "SUPERADMIN scale up":
            mock_endpoint = MagicMock(
                id=scenario.input.service_id,
                routings=[MagicMock() for _ in range(expected.current_route_count)],
            )
            mock_get_endpoint_by_id_force_scale.return_value = mock_endpoint
            mock_update_endpoint_replicas_force.return_value = True

        elif scenario.description == "non-existent service":
            if scenario.input.requester_ctx.user_role == UserRole.SUPERADMIN:
                mock_get_endpoint_by_id_force_scale.return_value = None
            else:
                mock_get_endpoint_by_id_validated_scale.return_value = None

        elif scenario.description == "update operation failed":
            mock_endpoint = MagicMock(
                id=scenario.input.service_id,
                routings=[MagicMock() for _ in range(2)],
            )
            mock_get_endpoint_by_id_validated_scale.return_value = mock_endpoint
            mock_update_endpoint_replicas_validated.return_value = False

        async def scale_service_replicas(action: ScaleServiceReplicasAction):
            return await auto_scaling_processors.scale_service_replicas.wait_for_complete(action)

        await scenario.test(scale_service_replicas)
