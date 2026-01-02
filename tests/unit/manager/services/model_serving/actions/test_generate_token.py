import uuid
from datetime import datetime
from typing import cast
from unittest.mock import AsyncMock, MagicMock, patch

import pytest
from aioresponses import aioresponses

from ai.backend.common.data.endpoint.types import EndpointStatus
from ai.backend.manager.data.model_serving.types import EndpointTokenData, RequesterCtx
from ai.backend.manager.models.user import UserRole
from ai.backend.manager.services.model_serving.actions.generate_token import (
    GenerateTokenAction,
    GenerateTokenActionResult,
)
from ai.backend.manager.services.model_serving.processors.model_serving import (
    ModelServingProcessors,
)

from ...utils import ScenarioBase


@pytest.fixture
def mock_check_requester_access_token(mocker, model_serving_service):
    mock = mocker.patch.object(
        model_serving_service,
        "check_requester_access",
        new_callable=AsyncMock,
    )
    mock.return_value = None
    return mock


@pytest.fixture
def mock_get_endpoint_by_id_force_token(mocker, mock_repositories):
    mock = mocker.patch.object(
        mock_repositories.admin_repository,
        "get_endpoint_by_id_force",
        new_callable=AsyncMock,
    )
    return mock


@pytest.fixture
def mock_create_endpoint_token_force(mocker, mock_repositories):
    mock = mocker.patch.object(
        mock_repositories.admin_repository,
        "create_endpoint_token_force",
        new_callable=AsyncMock,
    )
    return mock


@pytest.fixture
def mock_get_endpoint_by_id_validated_token(mocker, mock_repositories):
    mock = mocker.patch.object(
        mock_repositories.repository,
        "get_endpoint_by_id_validated",
        new_callable=AsyncMock,
    )
    return mock


@pytest.fixture
def mock_create_endpoint_token_validated(mocker, mock_repositories):
    mock = mocker.patch.object(
        mock_repositories.repository,
        "create_endpoint_token_validated",
        new_callable=AsyncMock,
    )
    return mock


@pytest.fixture
def mock_get_scaling_group_info_token(mocker, mock_repositories):
    mock = mocker.patch.object(
        mock_repositories.repository,
        "get_scaling_group_info",
        new_callable=AsyncMock,
    )
    return mock


class TestGenerateToken:
    @pytest.mark.parametrize(
        "scenario",
        [
            ScenarioBase.success(
                "regular token generation",
                GenerateTokenAction(
                    requester_ctx=RequesterCtx(
                        is_authorized=True,
                        user_id=uuid.UUID("00000000-0000-0000-0000-000000000001"),
                        user_role=UserRole.USER,
                        domain_name="default",
                    ),
                    service_id=uuid.UUID("dddddddd-dddd-dddd-dddd-dddddddddddd"),
                    duration=None,
                    valid_until=None,
                    expires_at=int(datetime.utcnow().timestamp()) + 86400,
                ),
                GenerateTokenActionResult(
                    data=EndpointTokenData(
                        id=uuid.UUID("12345678-1234-1234-1234-123456789012"),
                        token="jwt_token_example",
                        endpoint=uuid.UUID("dddddddd-dddd-dddd-dddd-dddddddddddd"),
                        session_owner=uuid.UUID("00000000-0000-0000-0000-000000000001"),
                        domain="default",
                        project=uuid.UUID("00000000-0000-0000-0000-000000000002"),
                        created_at=datetime.utcnow(),
                    ),
                ),
            ),
            ScenarioBase.success(
                "unlimited token",
                GenerateTokenAction(
                    requester_ctx=RequesterCtx(
                        is_authorized=True,
                        user_id=uuid.UUID("00000000-0000-0000-0000-000000000001"),
                        user_role=UserRole.USER,
                        domain_name="default",
                    ),
                    service_id=uuid.UUID("eeeeeeee-eeee-eeee-eeee-eeeeeeeeeeee"),
                    duration=None,
                    valid_until=None,
                    expires_at=0,  # No expiry
                ),
                GenerateTokenActionResult(
                    data=EndpointTokenData(
                        id=uuid.UUID("12345678-1234-1234-1234-123456789013"),
                        token="jwt_token_unlimited",
                        endpoint=uuid.UUID("eeeeeeee-eeee-eeee-eeee-eeeeeeeeeeee"),
                        session_owner=uuid.UUID("00000000-0000-0000-0000-000000000001"),
                        domain="default",
                        project=uuid.UUID("00000000-0000-0000-0000-000000000002"),
                        created_at=datetime.utcnow(),
                    ),
                ),
            ),
            ScenarioBase.success(
                "limited scope token",
                GenerateTokenAction(
                    requester_ctx=RequesterCtx(
                        is_authorized=True,
                        user_id=uuid.UUID("00000000-0000-0000-0000-000000000001"),
                        user_role=UserRole.USER,
                        domain_name="default",
                    ),
                    service_id=uuid.UUID("ffffffff-ffff-ffff-ffff-ffffffffffff"),
                    duration=None,
                    valid_until=None,
                    expires_at=int(datetime.utcnow().timestamp()) + 3600,
                ),
                GenerateTokenActionResult(
                    data=EndpointTokenData(
                        id=uuid.UUID("12345678-1234-1234-1234-123456789014"),
                        token="jwt_token_restricted",
                        endpoint=uuid.UUID("ffffffff-ffff-ffff-ffff-ffffffffffff"),
                        session_owner=uuid.UUID("00000000-0000-0000-0000-000000000001"),
                        domain="default",
                        project=uuid.UUID("00000000-0000-0000-0000-000000000002"),
                        created_at=datetime.utcnow(),
                    ),
                ),
            ),
        ],
    )
    @pytest.mark.asyncio
    async def test_generate_token(
        self,
        scenario: ScenarioBase[GenerateTokenAction, GenerateTokenActionResult],
        model_serving_processors: ModelServingProcessors,
        mock_check_requester_access_token,
        mock_get_endpoint_by_id_force_token,
        mock_create_endpoint_token_force,
        mock_get_endpoint_by_id_validated_token,
        mock_create_endpoint_token_validated,
        mock_get_scaling_group_info_token,
    ):
        action = scenario.input
        expected = scenario.expected

        # Mock setup based on scenario data
        expected = cast(GenerateTokenActionResult, expected)
        mock_endpoint = MagicMock(
            id=action.service_id,
            status=EndpointStatus.READY,
            session_owner_id=expected.data.session_owner,
            domain=expected.data.domain,
            project=expected.data.project,
            resource_group="default",
        )

        mock_scaling_group = MagicMock(
            wsproxy_addr="http://test-wsproxy:8080", wsproxy_api_token="test-api-token"
        )

        mock_token_data = MagicMock(
            id=expected.data.id,
            token=expected.data.token,
            endpoint=expected.data.endpoint,
            session_owner=expected.data.session_owner,
            domain=expected.data.domain,
            project=expected.data.project,
            created_at=expected.data.created_at,
        )

        # Setup repository mocks based on user role
        if action.requester_ctx.user_role == UserRole.SUPERADMIN:
            mock_get_endpoint_by_id_force_token.return_value = mock_endpoint
            mock_create_endpoint_token_force.return_value = mock_token_data
        else:
            mock_get_endpoint_by_id_validated_token.return_value = mock_endpoint
            mock_create_endpoint_token_validated.return_value = mock_token_data

        mock_get_scaling_group_info_token.return_value = mock_scaling_group

        # TODO: Change using aioresponses to mocking client layer after refactoring service layer
        with aioresponses() as mock_http:
            # HTTP response mock setup
            expected_url = (
                f"{mock_scaling_group.wsproxy_addr}/v2/endpoints/{action.service_id}/token"
            )
            mock_http.post(expected_url, payload={"token": expected.data.token}, status=200)

            with patch("uuid.uuid4", return_value=expected.data.id):

                async def generate_token(action: GenerateTokenAction):
                    return await model_serving_processors.generate_token.wait_for_complete(action)

                await scenario.test(generate_token)
