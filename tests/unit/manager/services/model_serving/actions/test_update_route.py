import uuid
from unittest.mock import AsyncMock, MagicMock

import aiohttp
import pytest

from ai.backend.common.contexts.user import with_user
from ai.backend.common.data.user.types import UserData
from ai.backend.manager.errors.service import ModelServiceNotFound
from ai.backend.manager.models.user import UserRole
from ai.backend.manager.services.model_serving.actions.update_route import (
    UpdateRouteAction,
    UpdateRouteActionResult,
)
from ai.backend.manager.services.model_serving.processors.model_serving import (
    ModelServingProcessors,
)
from ai.backend.testutils.scenario import ScenarioBase


@pytest.fixture
def mock_check_user_access_update_route(mocker, model_serving_service):
    mock = mocker.patch.object(
        model_serving_service,
        "check_user_access",
        new_callable=AsyncMock,
    )
    mock.return_value = None
    return mock


@pytest.fixture
def mock_get_endpoint_access_validation_data_update_route(mocker, mock_repositories):
    return mocker.patch.object(
        mock_repositories.repository,
        "get_endpoint_access_validation_data",
        new_callable=AsyncMock,
    )


@pytest.fixture
def mock_update_route_traffic(mocker, mock_repositories):
    return mocker.patch.object(
        mock_repositories.repository,
        "update_route_traffic",
        new_callable=AsyncMock,
    )


@pytest.fixture
def mock_get_endpoint_for_appproxy_update(mocker, mock_repositories):
    return mocker.patch.object(
        mock_repositories.repository,
        "get_endpoint_for_appproxy_update",
        new_callable=AsyncMock,
    )


@pytest.fixture
def mock_notify_endpoint_route_update_to_appproxy(mocker, mock_agent_registry):
    mock = mocker.patch.object(
        mock_agent_registry,
        "notify_endpoint_route_update_to_appproxy",
        new_callable=AsyncMock,
    )
    mock.return_value = None
    return mock


class TestUpdateRoute:
    @pytest.mark.parametrize(
        ("scenario", "user_data"),
        [
            (
                ScenarioBase.success(
                    "weighted routing",
                    UpdateRouteAction(
                        service_id=uuid.UUID("55555555-6666-7777-8888-999999999999"),
                        route_id=uuid.UUID("11111111-1111-1111-1111-111111111111"),
                        traffic_ratio=0.7,
                    ),
                    UpdateRouteActionResult(success=True),
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
                    "canary deployment",
                    UpdateRouteAction(
                        service_id=uuid.UUID("66666666-7777-8888-9999-aaaaaaaaaaaa"),
                        route_id=uuid.UUID("22222222-2222-2222-2222-222222222222"),
                        traffic_ratio=0.95,
                    ),
                    UpdateRouteActionResult(success=True),
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
                    "SUPERADMIN blue-green deployment",
                    UpdateRouteAction(
                        service_id=uuid.UUID("77777777-8888-9999-aaaa-bbbbbbbbbbbb"),
                        route_id=uuid.UUID("33333333-3333-3333-3333-333333333333"),
                        traffic_ratio=1.0,
                    ),
                    UpdateRouteActionResult(success=True),
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
    async def test_update_route(
        self,
        scenario: ScenarioBase[UpdateRouteAction, UpdateRouteActionResult],
        user_data: UserData,
        model_serving_processors: ModelServingProcessors,
        mock_check_user_access_update_route,
        mock_get_endpoint_access_validation_data_update_route,
        mock_update_route_traffic,
        mock_get_endpoint_for_appproxy_update,
        mock_notify_endpoint_route_update_to_appproxy,
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

        async def update_route(action: UpdateRouteAction):
            return await model_serving_processors.update_route.wait_for_complete(action)

        with with_user(user_data):
            await scenario.test(update_route)

    @pytest.mark.parametrize(
        ("scenario", "user_data"),
        [
            (
                ScenarioBase.failure(
                    "non-existent route",
                    UpdateRouteAction(
                        service_id=uuid.UUID("55555555-6666-7777-8888-999999999999"),
                        route_id=uuid.UUID("99999999-9999-9999-9999-999999999999"),
                        traffic_ratio=0.5,
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
        ],
    )
    @pytest.mark.asyncio
    async def test_update_route_failure(
        self,
        scenario: ScenarioBase[UpdateRouteAction, Exception],
        user_data: UserData,
        model_serving_processors: ModelServingProcessors,
        mock_check_user_access_update_route,
        mock_get_endpoint_access_validation_data_update_route,
        mock_update_route_traffic,
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

        async def update_route(action: UpdateRouteAction):
            return await model_serving_processors.update_route.wait_for_complete(action)

        with with_user(user_data):
            await scenario.test(update_route)

    @pytest.mark.asyncio
    async def test_update_route_appproxy_failure(
        self,
        model_serving_processors: ModelServingProcessors,
        mock_check_user_access_update_route,
        mock_get_endpoint_access_validation_data_update_route,
        mock_update_route_traffic,
        mock_get_endpoint_for_appproxy_update,
        mock_notify_endpoint_route_update_to_appproxy,
    ) -> None:
        user_data = UserData(
            user_id=uuid.UUID("00000000-0000-0000-0000-000000000001"),
            is_authorized=True,
            is_admin=False,
            is_superadmin=False,
            role=UserRole.USER.value,
            domain_name="default",
        )
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
        with with_user(user_data):
            with pytest.raises(aiohttp.ClientError, match="Connection failed"):
                await model_serving_processors.update_route.wait_for_complete(action)
