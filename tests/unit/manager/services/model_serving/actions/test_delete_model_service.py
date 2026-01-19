import uuid
from unittest.mock import AsyncMock, MagicMock

import pytest

from ai.backend.common.contexts.user import with_user
from ai.backend.common.data.user.types import UserData
from ai.backend.manager.errors.service import ModelServiceNotFound
from ai.backend.manager.models.user import UserRole
from ai.backend.manager.services.model_serving.actions.delete_model_service import (
    DeleteModelServiceAction,
    DeleteModelServiceActionResult,
)
from ai.backend.manager.services.model_serving.processors.model_serving import (
    ModelServingProcessors,
)
from ai.backend.testutils.scenario import ScenarioBase


@pytest.fixture
def mock_get_endpoint_by_id(mocker, mock_repositories):
    return mocker.patch.object(
        mock_repositories.repository,
        "get_endpoint_by_id",
        new_callable=AsyncMock,
    )


@pytest.fixture
def mock_get_endpoint_access_validation_data(mocker, mock_repositories):
    return mocker.patch.object(
        mock_repositories.repository,
        "get_endpoint_access_validation_data",
        new_callable=AsyncMock,
    )


@pytest.fixture
def mock_update_endpoint_lifecycle(mocker, mock_repositories):
    return mocker.patch.object(
        mock_repositories.repository,
        "update_endpoint_lifecycle",
        new_callable=AsyncMock,
    )


@pytest.fixture
def mock_check_user_access(mocker, model_serving_service):
    mock = mocker.patch.object(
        model_serving_service,
        "check_user_access",
        new_callable=AsyncMock,
    )
    mock.return_value = None
    return mock


class TestDeleteModelService:
    @pytest.mark.parametrize(
        ("scenario", "user_data"),
        [
            (
                ScenarioBase.success(
                    "successful model deletion (user request)",
                    DeleteModelServiceAction(
                        service_id=uuid.UUID("cccccccc-dddd-eeee-ffff-111111111111"),
                    ),
                    DeleteModelServiceActionResult(
                        success=True,
                    ),
                ),
                UserData(
                    user_id=uuid.UUID("00000000-0000-0000-0000-000000000001"),
                    is_authorized=True,
                    is_admin=False,
                    is_superadmin=False,
                    role=UserRole.USER.value,
                    domain_name="default",
                ),
            ),
            (
                ScenarioBase.failure(
                    "non-existent model (user request)",
                    DeleteModelServiceAction(
                        service_id=uuid.UUID("dddddddd-eeee-ffff-1111-222222222222"),
                    ),
                    ModelServiceNotFound,
                ),
                UserData(
                    user_id=uuid.UUID("00000000-0000-0000-0000-000000000001"),
                    is_authorized=True,
                    is_admin=False,
                    is_superadmin=False,
                    role=UserRole.USER.value,
                    domain_name="default",
                ),
            ),
            (
                ScenarioBase.success(
                    "successful model deletion (superadmin request)",
                    DeleteModelServiceAction(
                        service_id=uuid.UUID("cccccccc-dddd-eeee-ffff-111111111111"),
                    ),
                    DeleteModelServiceActionResult(
                        success=True,
                    ),
                ),
                UserData(
                    user_id=uuid.UUID("00000000-0000-0000-0000-000000000001"),
                    is_authorized=True,
                    is_admin=False,
                    is_superadmin=True,
                    role=UserRole.SUPERADMIN.value,
                    domain_name="default",
                ),
            ),
            (
                ScenarioBase.failure(
                    "non-existent model (superadmin request)",
                    DeleteModelServiceAction(
                        service_id=uuid.UUID("dddddddd-eeee-ffff-1111-222222222222"),
                    ),
                    ModelServiceNotFound,
                ),
                UserData(
                    user_id=uuid.UUID("00000000-0000-0000-0000-000000000001"),
                    is_authorized=True,
                    is_admin=False,
                    is_superadmin=True,
                    role=UserRole.SUPERADMIN.value,
                    domain_name="default",
                ),
            ),
        ],
    )
    @pytest.mark.asyncio
    async def test_delete_model_service(
        self,
        scenario: ScenarioBase[DeleteModelServiceAction, DeleteModelServiceActionResult],
        user_data: UserData,
        model_serving_processors: ModelServingProcessors,
        mock_get_endpoint_by_id,
        mock_get_endpoint_access_validation_data,
        mock_update_endpoint_lifecycle,
        mock_check_user_access,
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

        async def delete_model_service(action: DeleteModelServiceAction):
            return await model_serving_processors.delete_model_service.wait_for_complete(action)

        with with_user(user_data):
            await scenario.test(delete_model_service)
