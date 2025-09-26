import uuid
from unittest.mock import AsyncMock, MagicMock

import pytest

from ai.backend.manager.data.model_serving.types import RequesterCtx
from ai.backend.manager.errors.service import ModelServiceNotFound
from ai.backend.manager.models.user import UserRole
from ai.backend.manager.services.model_serving.actions.delete_model_service import (
    DeleteModelServiceAction,
    DeleteModelServiceActionResult,
)
from ai.backend.manager.services.model_serving.processors.model_serving import (
    ModelServingProcessors,
)

from ...utils import ScenarioBase


@pytest.fixture
def mock_get_endpoint_by_id_validated(mocker, mock_repositories):
    mock = mocker.patch.object(
        mock_repositories.repository,
        "get_endpoint_by_id_validated",
        new_callable=AsyncMock,
    )
    return mock


@pytest.fixture
def mock_update_endpoint_lifecycle_validated(mocker, mock_repositories):
    mock = mocker.patch.object(
        mock_repositories.repository,
        "update_endpoint_lifecycle_validated",
        new_callable=AsyncMock,
    )
    return mock


@pytest.fixture
def mock_get_endpoint_by_id_force(mocker, mock_repositories):
    mock = mocker.patch.object(
        mock_repositories.admin_repository,
        "get_endpoint_by_id_force",
        new_callable=AsyncMock,
    )
    return mock


@pytest.fixture
def mock_update_endpoint_lifecycle_force(mocker, mock_repositories):
    mock = mocker.patch.object(
        mock_repositories.admin_repository,
        "update_endpoint_lifecycle_force",
        new_callable=AsyncMock,
    )
    return mock


@pytest.fixture
def mock_check_requester_access(mocker, model_serving_service):
    mock = mocker.patch.object(
        model_serving_service,
        "check_requester_access",
        new_callable=AsyncMock,
    )
    mock.return_value = None
    return mock


class TestDeleteModelService:
    @pytest.mark.parametrize(
        "scenario",
        [
            ScenarioBase.success(
                "successful model deletion (user request)",
                DeleteModelServiceAction(
                    service_id=uuid.UUID("cccccccc-dddd-eeee-ffff-111111111111"),
                    requester_ctx=RequesterCtx(
                        is_authorized=True,
                        user_id=uuid.UUID("00000000-0000-0000-0000-000000000001"),
                        user_role=UserRole.USER,
                        domain_name="default",
                    ),
                ),
                DeleteModelServiceActionResult(
                    success=True,
                ),
            ),
            ScenarioBase.failure(
                "non-existent model (user request)",
                DeleteModelServiceAction(
                    service_id=uuid.UUID("dddddddd-eeee-ffff-1111-222222222222"),
                    requester_ctx=RequesterCtx(
                        is_authorized=True,
                        user_id=uuid.UUID("00000000-0000-0000-0000-000000000001"),
                        user_role=UserRole.USER,
                        domain_name="default",
                    ),
                ),
                ModelServiceNotFound,
            ),
            ScenarioBase.success(
                "successful model deletion (superadmin request)",
                DeleteModelServiceAction(
                    service_id=uuid.UUID("cccccccc-dddd-eeee-ffff-111111111111"),
                    requester_ctx=RequesterCtx(
                        is_authorized=True,
                        user_id=uuid.UUID("00000000-0000-0000-0000-000000000001"),
                        user_role=UserRole.SUPERADMIN,
                        domain_name="default",
                    ),
                ),
                DeleteModelServiceActionResult(
                    success=True,
                ),
            ),
            ScenarioBase.failure(
                "non-existent model (superadmin request)",
                DeleteModelServiceAction(
                    service_id=uuid.UUID("dddddddd-eeee-ffff-1111-222222222222"),
                    requester_ctx=RequesterCtx(
                        is_authorized=True,
                        user_id=uuid.UUID("00000000-0000-0000-0000-000000000001"),
                        user_role=UserRole.SUPERADMIN,
                        domain_name="default",
                    ),
                ),
                ModelServiceNotFound,
            ),
        ],
    )
    @pytest.mark.asyncio
    async def test_delete_model_service(
        self,
        scenario: ScenarioBase[DeleteModelServiceAction, DeleteModelServiceActionResult],
        model_serving_processors: ModelServingProcessors,
        mock_get_endpoint_by_id_validated,
        mock_update_endpoint_lifecycle_validated,
        mock_get_endpoint_by_id_force,
        mock_update_endpoint_lifecycle_force,
        mock_check_requester_access,
    ):
        mock_endpoint = MagicMock(routings=[])

        # Mock repository responses based on scenario
        if scenario.description == "successful model deletion (user request)":
            mock_get_endpoint_by_id_validated.return_value = mock_endpoint
            mock_update_endpoint_lifecycle_validated.return_value = None

        elif scenario.description == "non-existent model (user request)":
            mock_get_endpoint_by_id_validated.return_value = None

        elif scenario.description == "successful model deletion (superadmin request)":
            mock_get_endpoint_by_id_force.return_value = mock_endpoint
            mock_update_endpoint_lifecycle_force.return_value = None

        elif scenario.description == "non-existent model (superadmin request)":
            mock_get_endpoint_by_id_force.return_value = None

        async def delete_model_service(action: DeleteModelServiceAction):
            return await model_serving_processors.delete_model_service.wait_for_complete(action)

        await scenario.test(delete_model_service)
