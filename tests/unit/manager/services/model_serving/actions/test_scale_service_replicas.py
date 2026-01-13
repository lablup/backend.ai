import uuid
from typing import cast
from unittest.mock import AsyncMock, MagicMock

import pytest

from ai.backend.common.data.user.types import UserData
from ai.backend.manager.data.model_serving.types import UserRole
from ai.backend.manager.errors.service import EndpointAccessForbiddenError
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
from ai.backend.testutils.scenario import ScenarioBase


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
def mock_get_endpoint_by_id_scale(mocker, mock_repositories):
    return mocker.patch.object(
        mock_repositories.repository,
        "get_endpoint_by_id",
        new_callable=AsyncMock,
    )


@pytest.fixture
def mock_update_endpoint_replicas(mocker, mock_repositories):
    return mocker.patch.object(
        mock_repositories.repository,
        "update_endpoint_replicas",
        new_callable=AsyncMock,
    )


class TestScaleServiceReplicas:
    @pytest.mark.parametrize(
        "scenario",
        [
            ScenarioBase.success(
                "scale up",
                ScaleServiceReplicasAction(
                    user_data=UserData(
                        user_id=uuid.UUID("00000000-0000-0000-0000-000000000001"),
                        is_authorized=True,
                        is_admin=False,
                        is_superadmin=False,
                        role="user",
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
                    user_data=UserData(
                        user_id=uuid.UUID("00000000-0000-0000-0000-000000000001"),
                        is_authorized=True,
                        is_admin=False,
                        is_superadmin=False,
                        role="user",
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
                    user_data=UserData(
                        user_id=uuid.UUID("00000000-0000-0000-0000-000000000001"),
                        is_authorized=True,
                        is_admin=False,
                        is_superadmin=False,
                        role="user",
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
                    user_data=UserData(
                        user_id=uuid.UUID("00000000-0000-0000-0000-000000000001"),
                        is_authorized=True,
                        is_admin=False,
                        is_superadmin=True,
                        role="superadmin",
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
                    user_data=UserData(
                        user_id=uuid.UUID("00000000-0000-0000-0000-000000000001"),
                        is_authorized=True,
                        is_admin=False,
                        is_superadmin=False,
                        role="user",
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
                    user_data=UserData(
                        user_id=uuid.UUID("00000000-0000-0000-0000-000000000001"),
                        is_authorized=True,
                        is_admin=False,
                        is_superadmin=False,
                        role="user",
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
        mock_get_endpoint_by_id_scale,
        mock_update_endpoint_replicas,
    ):
        expected = cast(ScaleServiceReplicasActionResult, scenario.expected)
        action = scenario.input

        # Mock endpoint data based on scenario
        if scenario.description in ["scale up", "scale down", "zero scale", "SUPERADMIN scale up"]:
            mock_endpoint = MagicMock(
                id=action.service_id,
                routings=[MagicMock() for _ in range(expected.current_route_count)],
                session_owner_id=action.user_data.user_id,
                session_owner_role=UserRole.USER,
                domain=action.user_data.domain_name,
            )
            mock_get_endpoint_by_id_scale.return_value = mock_endpoint
            mock_update_endpoint_replicas.return_value = True

        elif scenario.description == "non-existent service":
            mock_get_endpoint_by_id_scale.return_value = None

        elif scenario.description == "update operation failed":
            mock_endpoint = MagicMock(
                id=action.service_id,
                routings=[MagicMock() for _ in range(2)],
                session_owner_id=action.user_data.user_id,
                session_owner_role=UserRole.USER,
                domain=action.user_data.domain_name,
            )
            mock_get_endpoint_by_id_scale.return_value = mock_endpoint
            mock_update_endpoint_replicas.return_value = False

        async def scale_service_replicas(action: ScaleServiceReplicasAction):
            return await auto_scaling_processors.scale_service_replicas.wait_for_complete(action)

        await scenario.test(scale_service_replicas)


class TestScaleServiceReplicasPermissions:
    """Tests for permission validation in scale_service_replicas."""

    @pytest.fixture
    def mock_get_endpoint_by_id(self, mocker, mock_repositories) -> AsyncMock:
        return mocker.patch.object(
            mock_repositories.repository,
            "get_endpoint_by_id",
            new_callable=AsyncMock,
        )

    @pytest.fixture
    def mock_update_endpoint_replicas(self, mocker, mock_repositories) -> AsyncMock:
        return mocker.patch.object(
            mock_repositories.repository,
            "update_endpoint_replicas",
            new_callable=AsyncMock,
        )

    @pytest.fixture
    def mock_check_requester_access(self, mocker, auto_scaling_service) -> AsyncMock:
        mock = mocker.patch.object(
            auto_scaling_service,
            "check_requester_access",
            new_callable=AsyncMock,
        )
        mock.return_value = None
        return mock

    @pytest.mark.asyncio
    async def test_user_cannot_scale_other_users_endpoint(
        self,
        auto_scaling_processors: ModelServingAutoScalingProcessors,
        mock_get_endpoint_by_id: AsyncMock,
        mock_update_endpoint_replicas: AsyncMock,
        mock_check_requester_access: AsyncMock,
    ) -> None:
        """USER should NOT be able to scale another user's endpoint."""
        owner_user_id = uuid.uuid4()
        other_user_id = uuid.uuid4()
        service_id = uuid.uuid4()

        mock_endpoint = MagicMock(
            id=service_id,
            routings=[MagicMock(), MagicMock()],
            session_owner_id=owner_user_id,
            session_owner_role=UserRole.USER,
            domain="default",
        )
        mock_get_endpoint_by_id.return_value = mock_endpoint

        action = ScaleServiceReplicasAction(
            service_id=service_id,
            user_data=UserData(
                user_id=other_user_id,  # Different from owner
                is_authorized=True,
                is_admin=False,
                is_superadmin=False,
                role="user",
                domain_name="default",
            ),
            max_session_count_per_model_session=100,
            to=5,
        )

        with pytest.raises(EndpointAccessForbiddenError):
            await auto_scaling_processors.scale_service_replicas.wait_for_complete(action)

    @pytest.mark.asyncio
    async def test_admin_cannot_scale_endpoint_in_different_domain(
        self,
        auto_scaling_processors: ModelServingAutoScalingProcessors,
        mock_get_endpoint_by_id: AsyncMock,
        mock_update_endpoint_replicas: AsyncMock,
        mock_check_requester_access: AsyncMock,
    ) -> None:
        """ADMIN should NOT be able to scale endpoint in different domain."""
        owner_user_id = uuid.uuid4()
        admin_user_id = uuid.uuid4()
        service_id = uuid.uuid4()

        mock_endpoint = MagicMock(
            id=service_id,
            routings=[MagicMock(), MagicMock()],
            session_owner_id=owner_user_id,
            session_owner_role=UserRole.USER,
            domain="domain-a",
        )
        mock_get_endpoint_by_id.return_value = mock_endpoint

        action = ScaleServiceReplicasAction(
            service_id=service_id,
            user_data=UserData(
                user_id=admin_user_id,
                is_authorized=True,
                is_admin=True,
                is_superadmin=False,
                role="admin",
                domain_name="domain-b",  # Different domain
            ),
            max_session_count_per_model_session=100,
            to=5,
        )

        with pytest.raises(EndpointAccessForbiddenError):
            await auto_scaling_processors.scale_service_replicas.wait_for_complete(action)

    @pytest.mark.asyncio
    async def test_admin_cannot_scale_superadmin_owned_endpoint(
        self,
        auto_scaling_processors: ModelServingAutoScalingProcessors,
        mock_get_endpoint_by_id: AsyncMock,
        mock_update_endpoint_replicas: AsyncMock,
        mock_check_requester_access: AsyncMock,
    ) -> None:
        """ADMIN should NOT be able to scale SUPERADMIN's endpoint even in same domain."""
        superadmin_owner_id = uuid.uuid4()
        admin_user_id = uuid.uuid4()
        service_id = uuid.uuid4()

        mock_endpoint = MagicMock(
            id=service_id,
            routings=[MagicMock(), MagicMock()],
            session_owner_id=superadmin_owner_id,
            session_owner_role=UserRole.SUPERADMIN,  # Owned by SUPERADMIN
            domain="default",
        )
        mock_get_endpoint_by_id.return_value = mock_endpoint

        action = ScaleServiceReplicasAction(
            service_id=service_id,
            user_data=UserData(
                user_id=admin_user_id,
                is_authorized=True,
                is_admin=True,
                is_superadmin=False,
                role="admin",
                domain_name="default",
            ),
            max_session_count_per_model_session=100,
            to=5,
        )

        with pytest.raises(EndpointAccessForbiddenError):
            await auto_scaling_processors.scale_service_replicas.wait_for_complete(action)
