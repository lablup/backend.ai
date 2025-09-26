import uuid
from typing import cast
from unittest.mock import AsyncMock, MagicMock

import pytest
from pydantic import HttpUrl

from ai.backend.manager.data.model_serving.types import CompactServiceInfo
from ai.backend.manager.models.routing import RouteStatus
from ai.backend.manager.services.model_serving.actions.list_model_service import (
    ListModelServiceAction,
    ListModelServiceActionResult,
)
from ai.backend.manager.services.model_serving.processors.model_serving import (
    ModelServingProcessors,
)

from ...utils import ScenarioBase


@pytest.fixture
def mock_list_endpoints_by_owner_validated(mocker, mock_repositories):
    mock = mocker.patch.object(
        mock_repositories.repository,
        "list_endpoints_by_owner_validated",
        new_callable=AsyncMock,
    )
    return mock


class TestListModelService:
    @pytest.mark.parametrize(
        "scenario",
        [
            ScenarioBase.success(
                "all model service list",
                ListModelServiceAction(
                    session_owener_id=uuid.UUID("00000000-0000-0000-0000-000000000001"),
                    name=None,
                ),
                ListModelServiceActionResult(
                    data=[
                        CompactServiceInfo(
                            id=uuid.UUID("88888888-9999-aaaa-bbbb-cccccccccccc"),
                            name="model-1-v1.0",
                            replicas=2,
                            desired_session_count=2,
                            active_route_count=2,
                            service_endpoint=HttpUrl(
                                "https://api.example.com/v1/models/model-1/v1.0"
                            ),
                            is_public=False,
                        ),
                        CompactServiceInfo(
                            id=uuid.UUID("99999999-aaaa-bbbb-cccc-dddddddddddd"),
                            name="model-2-v2.0",
                            replicas=3,
                            desired_session_count=3,
                            active_route_count=3,
                            service_endpoint=HttpUrl(
                                "https://api.example.com/v1/models/model-2/v2.0"
                            ),
                            is_public=False,
                        ),
                    ]
                ),
            ),
            ScenarioBase.success(
                "name filtered",
                ListModelServiceAction(
                    session_owener_id=uuid.UUID("00000000-0000-0000-0000-000000000001"),
                    name="project-model",
                ),
                ListModelServiceActionResult(
                    data=[
                        CompactServiceInfo(
                            id=uuid.UUID("bbbbbbbb-cccc-dddd-eeee-ffffffffffff"),
                            name="project-model",
                            replicas=1,
                            desired_session_count=1,
                            active_route_count=1,
                            service_endpoint=HttpUrl(
                                "https://api.example.com/v1/models/project-model/v1.0"
                            ),
                            is_public=False,
                        ),
                    ]
                ),
            ),
        ],
    )
    @pytest.mark.asyncio
    async def test_list_model_service(
        self,
        scenario: ScenarioBase[ListModelServiceAction, ListModelServiceActionResult],
        model_serving_processors: ModelServingProcessors,
        mock_list_endpoints_by_owner_validated,
    ):
        # Mock repository responses
        mock_endpoints = []
        expected = cast(ListModelServiceActionResult, scenario.expected)
        for endpoint_data in expected.data:
            mock_endpoint = MagicMock(
                id=endpoint_data.id,
                replicas=endpoint_data.replicas,
                desired_session_count=endpoint_data.replicas,
                routings=[
                    MagicMock(status=RouteStatus.HEALTHY)
                    for _ in range(endpoint_data.active_route_count)
                ],
                url=str(endpoint_data.service_endpoint),
                open_to_public=endpoint_data.is_public,
            )
            mock_endpoint.name = (
                endpoint_data.name
            )  # As 'name' is special attribute in MagicMock, we set it this way
            mock_endpoints.append(mock_endpoint)

        mock_list_endpoints_by_owner_validated.return_value = mock_endpoints

        async def list_model_service(action: ListModelServiceAction):
            return await model_serving_processors.list_model_service.wait_for_complete(action)

        await scenario.test(list_model_service)
