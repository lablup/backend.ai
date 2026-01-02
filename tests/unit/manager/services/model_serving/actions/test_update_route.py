import uuid
from unittest.mock import AsyncMock, MagicMock

import aiohttp
import pytest

from ai.backend.manager.data.model_serving.types import RequesterCtx
from ai.backend.manager.errors.service import ModelServiceNotFound
from ai.backend.manager.models.user import UserRole
from ai.backend.manager.services.model_serving.actions.update_route import (
    UpdateRouteAction,
    UpdateRouteActionResult,
)
from ai.backend.manager.services.model_serving.processors.model_serving import (
    ModelServingProcessors,
)

from ...utils import ScenarioBase


@pytest.fixture
def mock_check_requester_access_update_route(mocker, model_serving_service):
    mock = mocker.patch.object(
        model_serving_service,
        "check_requester_access",
        new_callable=AsyncMock,
    )
    mock.return_value = None
    return mock


@pytest.fixture
def mock_update_route_traffic_force(mocker, mock_repositories):
    mock = mocker.patch.object(
        mock_repositories.admin_repository,
        "update_route_traffic_force",
        new_callable=AsyncMock,
    )
    return mock


@pytest.fixture
def mock_update_route_traffic_validated(mocker, mock_repositories):
    mock = mocker.patch.object(
        mock_repositories.repository,
        "update_route_traffic_validated",
        new_callable=AsyncMock,
    )
    return mock


@pytest.fixture
def mock_get_endpoint_for_appproxy_update(mocker, mock_repositories):
    mock = mocker.patch.object(
        mock_repositories.repository,
        "get_endpoint_for_appproxy_update",
        new_callable=AsyncMock,
    )
    return mock


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
        "scenario",
        [
            ScenarioBase.success(
                "weighted routing",
                UpdateRouteAction(
                    requester_ctx=RequesterCtx(
                        is_authorized=True,
                        user_id=uuid.UUID("00000000-0000-0000-0000-000000000001"),
                        user_role=UserRole.USER,
                        domain_name="default",
                    ),
                    service_id=uuid.UUID("55555555-6666-7777-8888-999999999999"),
                    route_id=uuid.UUID("11111111-1111-1111-1111-111111111111"),
                    traffic_ratio=0.7,
                ),
                UpdateRouteActionResult(success=True),
            ),
            ScenarioBase.success(
                "canary deployment",
                UpdateRouteAction(
                    requester_ctx=RequesterCtx(
                        is_authorized=True,
                        user_id=uuid.UUID("00000000-0000-0000-0000-000000000001"),
                        user_role=UserRole.USER,
                        domain_name="default",
                    ),
                    service_id=uuid.UUID("66666666-7777-8888-9999-aaaaaaaaaaaa"),
                    route_id=uuid.UUID("22222222-2222-2222-2222-222222222222"),
                    traffic_ratio=0.95,
                ),
                UpdateRouteActionResult(success=True),
            ),
            ScenarioBase.success(
                "SUPERADMIN blue-green deployment",
                UpdateRouteAction(
                    requester_ctx=RequesterCtx(
                        is_authorized=True,
                        user_id=uuid.UUID("00000000-0000-0000-0000-000000000001"),
                        user_role=UserRole.SUPERADMIN,
                        domain_name="default",
                    ),
                    service_id=uuid.UUID("77777777-8888-9999-aaaa-bbbbbbbbbbbb"),
                    route_id=uuid.UUID("33333333-3333-3333-3333-333333333333"),
                    traffic_ratio=1.0,
                ),
                UpdateRouteActionResult(success=True),
            ),
        ],
    )
    @pytest.mark.asyncio
    async def test_update_route(
        self,
        scenario: ScenarioBase[UpdateRouteAction, UpdateRouteActionResult],
        model_serving_processors: ModelServingProcessors,
        mock_check_requester_access_update_route,
        mock_update_route_traffic_force,
        mock_update_route_traffic_validated,
        mock_get_endpoint_for_appproxy_update,
        mock_notify_endpoint_route_update_to_appproxy,
    ):
        # Mock endpoint data for route update
        mock_endpoint_data = MagicMock(
            id=scenario.input.service_id,
            route_id=scenario.input.route_id,
            traffic_ratio=scenario.input.traffic_ratio,
        )

        # Mock endpoint row for AppProxy update
        mock_endpoint_row = MagicMock(
            id=scenario.input.service_id,
            url="https://api.example.com/v1/models/test-model",
            routings=[
                MagicMock(
                    id=scenario.input.route_id,
                    traffic_ratio=scenario.input.traffic_ratio,
                    session=uuid.UUID("aaaaaaaa-bbbb-cccc-dddd-eeeeeeeeeeee"),
                )
            ],
        )

        # Mock repository based on user role
        if scenario.input.requester_ctx.user_role == UserRole.SUPERADMIN:
            mock_update_route_traffic_force.return_value = mock_endpoint_data
        else:
            mock_update_route_traffic_validated.return_value = mock_endpoint_data

        # Mock AppProxy related methods
        mock_get_endpoint_for_appproxy_update.return_value = mock_endpoint_row

        async def update_route(action: UpdateRouteAction):
            return await model_serving_processors.update_route.wait_for_complete(action)

        await scenario.test(update_route)

    @pytest.mark.parametrize(
        "scenario",
        [
            ScenarioBase.failure(
                "non-existent route",
                UpdateRouteAction(
                    requester_ctx=RequesterCtx(
                        is_authorized=True,
                        user_id=uuid.UUID("00000000-0000-0000-0000-000000000001"),
                        user_role=UserRole.USER,
                        domain_name="default",
                    ),
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
        model_serving_processors: ModelServingProcessors,
        mock_check_requester_access_update_route,
        mock_update_route_traffic_validated,
    ):
        # Mock repository to return None (route not found)
        mock_update_route_traffic_validated.return_value = None

        async def update_route(action: UpdateRouteAction):
            return await model_serving_processors.update_route.wait_for_complete(action)

        await scenario.test(update_route)

    @pytest.mark.asyncio
    async def test_update_route_appproxy_failure(
        self,
        model_serving_processors: ModelServingProcessors,
        mock_check_requester_access_update_route,
        mock_update_route_traffic_validated,
        mock_get_endpoint_for_appproxy_update,
        mock_notify_endpoint_route_update_to_appproxy,
    ):
        action = UpdateRouteAction(
            requester_ctx=RequesterCtx(
                is_authorized=True,
                user_id=uuid.UUID("00000000-0000-0000-0000-000000000001"),
                user_role=UserRole.USER,
                domain_name="default",
            ),
            service_id=uuid.UUID("55555555-6666-7777-8888-999999999999"),
            route_id=uuid.UUID("11111111-1111-1111-1111-111111111111"),
            traffic_ratio=0.7,
        )

        # Mock successful route update
        mock_update_route_traffic_validated.return_value = MagicMock(id=action.service_id)
        mock_get_endpoint_for_appproxy_update.return_value = MagicMock(id=action.service_id)

        # Mock AppProxy communication failure
        mock_notify_endpoint_route_update_to_appproxy.side_effect = aiohttp.ClientError(
            "Connection failed"
        )

        # AppProxy failure should propagate as exception
        with pytest.raises(aiohttp.ClientError, match="Connection failed"):
            await model_serving_processors.update_route.wait_for_complete(action)
