import uuid
from datetime import UTC, datetime
from typing import cast
from unittest.mock import AsyncMock, MagicMock

import pytest

from ai.backend.common.data.user.types import UserData
from ai.backend.manager.data.model_serving.types import ErrorInfo
from ai.backend.manager.models.routing import RouteStatus
from ai.backend.manager.models.user import UserRole
from ai.backend.manager.services.model_serving.actions.list_errors import (
    ListErrorsAction,
    ListErrorsActionResult,
)
from ai.backend.manager.services.model_serving.processors.model_serving import (
    ModelServingProcessors,
)
from ai.backend.testutils.scenario import ScenarioBase


@pytest.fixture
def mock_check_user_access_list_errors(mocker, model_serving_service):
    mock = mocker.patch.object(
        model_serving_service,
        "check_user_access",
        new_callable=AsyncMock,
    )
    mock.return_value = None
    return mock


@pytest.fixture
def mock_get_endpoint_by_id_list_errors(mocker, mock_repositories):
    return mocker.patch.object(
        mock_repositories.repository,
        "get_endpoint_by_id",
        new_callable=AsyncMock,
    )


@pytest.fixture
def mock_get_endpoint_access_validation_data_list_errors(mocker, mock_repositories):
    return mocker.patch.object(
        mock_repositories.repository,
        "get_endpoint_access_validation_data",
        new_callable=AsyncMock,
    )


class TestListErrors:
    @pytest.mark.parametrize(
        "scenario",
        [
            ScenarioBase.success(
                "recent errors lookup",
                ListErrorsAction(
                    user_data=UserData(
                        user_id=uuid.UUID("00000000-0000-0000-0000-000000000001"),
                        is_authorized=True,
                        is_admin=False,
                        is_superadmin=False,
                        role=UserRole.USER.value,
                        domain_name="default",
                    ),
                    service_id=uuid.UUID("11111111-2222-3333-4444-555555555555"),
                ),
                ListErrorsActionResult(
                    error_info=[
                        ErrorInfo(
                            session_id=uuid.UUID("aaaaaaaa-bbbb-cccc-dddd-eeeeeeeeeeee"),
                            error={
                                "timestamp": datetime.now(tz=UTC).isoformat(),
                                "error_type": "OOMKilled",
                                "message": "Container killed due to out of memory",
                            },
                        ),
                        ErrorInfo(
                            session_id=uuid.UUID("bbbbbbbb-cccc-dddd-eeee-ffffffffffff"),
                            error={
                                "timestamp": datetime.now(tz=UTC).isoformat(),
                                "error_type": "ImagePullError",
                                "message": "Failed to pull image",
                            },
                        ),
                    ],
                    retries=0,
                ),
            ),
            ScenarioBase.success(
                "error type filtered",
                ListErrorsAction(
                    user_data=UserData(
                        user_id=uuid.UUID("00000000-0000-0000-0000-000000000001"),
                        is_authorized=True,
                        is_admin=False,
                        is_superadmin=False,
                        role=UserRole.USER.value,
                        domain_name="default",
                    ),
                    service_id=uuid.UUID("22222222-3333-4444-5555-666666666666"),
                ),
                ListErrorsActionResult(
                    error_info=[
                        ErrorInfo(
                            session_id=uuid.UUID("cccccccc-dddd-eeee-ffff-111111111111"),
                            error={
                                "timestamp": datetime.now(tz=UTC).isoformat(),
                                "error_type": "OOMKilled",
                                "message": "Container killed due to out of memory",
                            },
                        ),
                    ],
                    retries=0,
                ),
            ),
        ],
    )
    @pytest.mark.asyncio
    async def test_list_errors(
        self,
        scenario: ScenarioBase[ListErrorsAction, ListErrorsActionResult],
        model_serving_processors: ModelServingProcessors,
        mock_check_user_access_list_errors,
        mock_get_endpoint_by_id_list_errors,
        mock_get_endpoint_access_validation_data_list_errors,
    ):
        # Mock repository responses
        expected = cast(ListErrorsActionResult, scenario.expected)
        action = scenario.input

        mock_validation_data = MagicMock(
            session_owner_id=action.user_data.user_id,
            session_owner_role=UserRole(action.user_data.role),
            domain=action.user_data.domain_name,
        )
        mock_get_endpoint_access_validation_data_list_errors.return_value = mock_validation_data

        mock_routings = [
            MagicMock(
                status=RouteStatus.FAILED_TO_START,
                error_data={
                    "session_id": error_info.session_id,
                    "errors": {
                        "timestamp": error_info.error["timestamp"],
                        "error_type": error_info.error["error_type"],
                        "message": error_info.error["message"],
                    },
                },
            )
            for error_info in expected.error_info
        ]
        mock_endpoint = MagicMock(
            id=scenario.input.service_id,
            routings=mock_routings,
            retries=expected.retries,
        )

        # Now uses single repository for all roles
        mock_get_endpoint_by_id_list_errors.return_value = mock_endpoint

        async def list_errors(action: ListErrorsAction):
            return await model_serving_processors.list_errors.wait_for_complete(action)

        await scenario.test(list_errors)
