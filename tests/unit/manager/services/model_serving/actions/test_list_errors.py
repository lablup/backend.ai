import uuid
from datetime import datetime
from typing import cast
from unittest.mock import AsyncMock, MagicMock

import pytest

from ai.backend.manager.data.model_serving.types import ErrorInfo, RequesterCtx
from ai.backend.manager.models.routing import RouteStatus
from ai.backend.manager.models.user import UserRole
from ai.backend.manager.services.model_serving.actions.list_errors import (
    ListErrorsAction,
    ListErrorsActionResult,
)
from ai.backend.manager.services.model_serving.processors.model_serving import (
    ModelServingProcessors,
)

from ...utils import ScenarioBase


@pytest.fixture
def mock_check_requester_access_list_errors(mocker, model_serving_service):
    mock = mocker.patch.object(
        model_serving_service,
        "check_requester_access",
        new_callable=AsyncMock,
    )
    mock.return_value = None
    return mock


@pytest.fixture
def mock_get_endpoint_by_id_force_list_errors(mocker, mock_repositories):
    mock = mocker.patch.object(
        mock_repositories.admin_repository,
        "get_endpoint_by_id_force",
        new_callable=AsyncMock,
    )
    return mock


@pytest.fixture
def mock_get_endpoint_by_id_validated_list_errors(mocker, mock_repositories):
    mock = mocker.patch.object(
        mock_repositories.repository,
        "get_endpoint_by_id_validated",
        new_callable=AsyncMock,
    )
    return mock


class TestListErrors:
    @pytest.mark.parametrize(
        "scenario",
        [
            ScenarioBase.success(
                "recent errors lookup",
                ListErrorsAction(
                    requester_ctx=RequesterCtx(
                        is_authorized=True,
                        user_id=uuid.UUID("00000000-0000-0000-0000-000000000001"),
                        user_role=UserRole.USER,
                        domain_name="default",
                    ),
                    service_id=uuid.UUID("11111111-2222-3333-4444-555555555555"),
                ),
                ListErrorsActionResult(
                    error_info=[
                        ErrorInfo(
                            session_id=uuid.UUID("aaaaaaaa-bbbb-cccc-dddd-eeeeeeeeeeee"),
                            error={
                                "timestamp": datetime.utcnow().isoformat(),
                                "error_type": "OOMKilled",
                                "message": "Container killed due to out of memory",
                            },
                        ),
                        ErrorInfo(
                            session_id=uuid.UUID("bbbbbbbb-cccc-dddd-eeee-ffffffffffff"),
                            error={
                                "timestamp": datetime.utcnow().isoformat(),
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
                    requester_ctx=RequesterCtx(
                        is_authorized=True,
                        user_id=uuid.UUID("00000000-0000-0000-0000-000000000001"),
                        user_role=UserRole.USER,
                        domain_name="default",
                    ),
                    service_id=uuid.UUID("22222222-3333-4444-5555-666666666666"),
                ),
                ListErrorsActionResult(
                    error_info=[
                        ErrorInfo(
                            session_id=uuid.UUID("cccccccc-dddd-eeee-ffff-111111111111"),
                            error={
                                "timestamp": datetime.utcnow().isoformat(),
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
        mock_check_requester_access_list_errors,
        mock_get_endpoint_by_id_force_list_errors,
        mock_get_endpoint_by_id_validated_list_errors,
    ):
        # Mock repository responses
        expected = cast(ListErrorsActionResult, scenario.expected)
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

        if scenario.input.requester_ctx.user_role == UserRole.SUPERADMIN:
            mock_get_endpoint_by_id_force_list_errors.return_value = mock_endpoint
        else:
            mock_get_endpoint_by_id_validated_list_errors.return_value = mock_endpoint

        async def list_errors(action: ListErrorsAction):
            return await model_serving_processors.list_errors.wait_for_complete(action)

        await scenario.test(list_errors)
