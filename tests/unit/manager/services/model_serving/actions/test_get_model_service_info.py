import uuid
from typing import cast
from unittest.mock import AsyncMock, MagicMock

import pytest
from pydantic import HttpUrl

from ai.backend.common.types import RuntimeVariant
from ai.backend.manager.data.model_serving.types import RequesterCtx, RouteInfo, ServiceInfo
from ai.backend.manager.models.user import UserRole
from ai.backend.manager.services.model_serving.actions.get_model_service_info import (
    GetModelServiceInfoAction,
    GetModelServiceInfoActionResult,
)
from ai.backend.manager.services.model_serving.processors.model_serving import (
    ModelServingProcessors,
)

from ...utils import ScenarioBase


@pytest.fixture
def mock_check_requester_access_get_info(mocker, model_serving_service):
    mock = mocker.patch.object(
        model_serving_service,
        "check_requester_access",
        new_callable=AsyncMock,
    )
    mock.return_value = None
    return mock


@pytest.fixture
def mock_get_endpoint_by_id_force_get_info(mocker, mock_repositories):
    mock = mocker.patch.object(
        mock_repositories.admin_repository,
        "get_endpoint_by_id_force",
        new_callable=AsyncMock,
    )
    return mock


@pytest.fixture
def mock_get_endpoint_by_id_validated_get_info(mocker, mock_repositories):
    mock = mocker.patch.object(
        mock_repositories.repository,
        "get_endpoint_by_id_validated",
        new_callable=AsyncMock,
    )
    return mock


class TestGetModelServiceInfo:
    @pytest.mark.parametrize(
        "scenario",
        [
            ScenarioBase.success(
                "full info lookup",
                GetModelServiceInfoAction(
                    requester_ctx=RequesterCtx(
                        is_authorized=True,
                        user_id=uuid.UUID("00000000-0000-0000-0000-000000000001"),
                        user_role=UserRole.USER,
                        domain_name="default",
                    ),
                    service_id=uuid.UUID("33333333-4444-5555-6666-777777777777"),
                ),
                GetModelServiceInfoActionResult(
                    data=ServiceInfo(
                        endpoint_id=uuid.UUID("33333333-4444-5555-6666-777777777777"),
                        model_id=uuid.UUID("11111111-1111-1111-1111-111111111111"),
                        extra_mounts=[],
                        name="test-model-v1.0",
                        model_definition_path=None,
                        replicas=3,
                        desired_session_count=3,
                        active_routes=[],
                        service_endpoint=HttpUrl(
                            "https://api.example.com/v1/models/test-model/v1.0"
                        ),
                        is_public=False,
                        runtime_variant=RuntimeVariant.CUSTOM,
                    ),
                ),
            ),
            ScenarioBase.success(
                "SUPERADMIN permission lookup",
                GetModelServiceInfoAction(
                    requester_ctx=RequesterCtx(
                        is_authorized=True,
                        user_id=uuid.UUID("00000000-0000-0000-0000-000000000001"),
                        user_role=UserRole.SUPERADMIN,
                        domain_name="default",
                    ),
                    service_id=uuid.UUID("44444444-5555-6666-7777-888888888888"),
                ),
                GetModelServiceInfoActionResult(
                    data=ServiceInfo(
                        endpoint_id=uuid.UUID("44444444-5555-6666-7777-888888888888"),
                        model_id=uuid.UUID("22222222-2222-2222-2222-222222222222"),
                        extra_mounts=[],
                        name="admin-model-v2.0",
                        model_definition_path="/path/to/model",
                        replicas=2,
                        desired_session_count=2,
                        active_routes=[
                            RouteInfo(
                                route_id=uuid.UUID("aaaaaaaa-bbbb-cccc-dddd-eeeeeeeeeeee"),
                                session_id=uuid.UUID("bbbbbbbb-cccc-dddd-eeee-ffffffffffff"),
                                traffic_ratio=100.0,
                            )
                        ],
                        service_endpoint=HttpUrl(
                            "https://api.example.com/v1/models/admin-model/v2.0"
                        ),
                        is_public=True,
                        runtime_variant=RuntimeVariant.CUSTOM,
                    ),
                ),
            ),
        ],
    )
    @pytest.mark.asyncio
    async def test_get_model_service_info(
        self,
        scenario: ScenarioBase[GetModelServiceInfoAction, GetModelServiceInfoActionResult],
        model_serving_processors: ModelServingProcessors,
        mock_check_requester_access_get_info,
        mock_get_endpoint_by_id_force_get_info,
        mock_get_endpoint_by_id_validated_get_info,
    ):
        # Mock repository responses
        expected = cast(GetModelServiceInfoActionResult, scenario.expected)
        mock_endpoint = MagicMock(
            id=expected.data.endpoint_id,
            model=expected.data.model_id,
            extra_mounts=[
                MagicMock(vfid=MagicMock(folder_id=mount_id))
                for mount_id in expected.data.extra_mounts
            ],
            model_definition_path=expected.data.model_definition_path,
            replicas=expected.data.replicas,
            routings=[
                MagicMock(
                    id=route.route_id,
                    session=route.session_id,
                    traffic_ratio=route.traffic_ratio,
                )
                for route in expected.data.active_routes
            ]
            if expected.data.active_routes
            else [],
            url=str(expected.data.service_endpoint) if expected.data.service_endpoint else None,
            open_to_public=expected.data.is_public,
            runtime_variant=expected.data.runtime_variant,
        )
        mock_endpoint.name = expected.data.name

        # Mock repository based on user role
        if scenario.input.requester_ctx.user_role == UserRole.SUPERADMIN:
            mock_get_endpoint_by_id_force_get_info.return_value = mock_endpoint
        else:
            mock_get_endpoint_by_id_validated_get_info.return_value = mock_endpoint

        async def get_model_service_info(action: GetModelServiceInfoAction):
            return await model_serving_processors.get_model_service_info.wait_for_complete(action)

        await scenario.test(get_model_service_info)
