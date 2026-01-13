import uuid
from unittest.mock import AsyncMock, MagicMock

import pytest

from ai.backend.common.data.user.types import UserData
from ai.backend.manager.data.model_serving.types import UserRole
from ai.backend.manager.errors.service import EndpointAccessForbiddenError, ModelServiceNotFound
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
def mock_update_endpoint_lifecycle(mocker, mock_repositories):
    return mocker.patch.object(
        mock_repositories.repository,
        "update_endpoint_lifecycle",
        new_callable=AsyncMock,
    )


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
                    user_data=UserData(
                        user_id=uuid.UUID("00000000-0000-0000-0000-000000000001"),
                        is_authorized=True,
                        is_admin=False,
                        is_superadmin=False,
                        role="user",
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
                    user_data=UserData(
                        user_id=uuid.UUID("00000000-0000-0000-0000-000000000001"),
                        is_authorized=True,
                        is_admin=False,
                        is_superadmin=False,
                        role="user",
                        domain_name="default",
                    ),
                ),
                ModelServiceNotFound,
            ),
            ScenarioBase.success(
                "successful model deletion (superadmin request)",
                DeleteModelServiceAction(
                    service_id=uuid.UUID("cccccccc-dddd-eeee-ffff-111111111111"),
                    user_data=UserData(
                        user_id=uuid.UUID("00000000-0000-0000-0000-000000000001"),
                        is_authorized=True,
                        is_admin=False,
                        is_superadmin=True,
                        role="superadmin",
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
                    user_data=UserData(
                        user_id=uuid.UUID("00000000-0000-0000-0000-000000000001"),
                        is_authorized=True,
                        is_admin=False,
                        is_superadmin=True,
                        role="superadmin",
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
        mock_get_endpoint_by_id,
        mock_update_endpoint_lifecycle,
        mock_check_requester_access,
    ):
        action = scenario.input
        mock_endpoint = MagicMock(
            routings=[],
            session_owner_id=action.user_data.user_id,
            session_owner_role=UserRole.USER,
            domain=action.user_data.domain_name,
        )

        # Mock repository responses based on scenario
        if "successful" in scenario.description:
            mock_get_endpoint_by_id.return_value = mock_endpoint
            mock_update_endpoint_lifecycle.return_value = None
        else:  # non-existent model
            mock_get_endpoint_by_id.return_value = None

        async def delete_model_service(action: DeleteModelServiceAction):
            return await model_serving_processors.delete_model_service.wait_for_complete(action)

        await scenario.test(delete_model_service)


class TestDeleteModelServicePermissions:
    """Tests for permission validation in delete_model_service."""

    @pytest.fixture
    def mock_get_endpoint_by_id(self, mocker, mock_repositories) -> AsyncMock:
        return mocker.patch.object(
            mock_repositories.repository,
            "get_endpoint_by_id",
            new_callable=AsyncMock,
        )

    @pytest.fixture
    def mock_update_endpoint_lifecycle(self, mocker, mock_repositories) -> AsyncMock:
        return mocker.patch.object(
            mock_repositories.repository,
            "update_endpoint_lifecycle",
            new_callable=AsyncMock,
        )

    @pytest.fixture
    def mock_check_requester_access(self, mocker, model_serving_service) -> AsyncMock:
        mock = mocker.patch.object(
            model_serving_service,
            "check_requester_access",
            new_callable=AsyncMock,
        )
        mock.return_value = None
        return mock

    @pytest.mark.asyncio
    async def test_user_cannot_delete_other_users_endpoint(
        self,
        model_serving_processors: ModelServingProcessors,
        mock_get_endpoint_by_id: AsyncMock,
        mock_update_endpoint_lifecycle: AsyncMock,
        mock_check_requester_access: AsyncMock,
    ) -> None:
        """USER should NOT be able to delete another user's endpoint."""
        owner_user_id = uuid.uuid4()
        other_user_id = uuid.uuid4()
        service_id = uuid.uuid4()

        # Endpoint owned by different user
        mock_endpoint = MagicMock(
            routings=[],
            session_owner_id=owner_user_id,
            session_owner_role=UserRole.USER,
            domain="default",
        )
        mock_get_endpoint_by_id.return_value = mock_endpoint

        action = DeleteModelServiceAction(
            service_id=service_id,
            user_data=UserData(
                user_id=other_user_id,  # Different from owner
                is_authorized=True,
                is_admin=False,
                is_superadmin=False,
                role="user",
                domain_name="default",
            ),
        )

        with pytest.raises(EndpointAccessForbiddenError):
            await model_serving_processors.delete_model_service.wait_for_complete(action)

    @pytest.mark.asyncio
    async def test_admin_cannot_delete_endpoint_in_different_domain(
        self,
        model_serving_processors: ModelServingProcessors,
        mock_get_endpoint_by_id: AsyncMock,
        mock_update_endpoint_lifecycle: AsyncMock,
        mock_check_requester_access: AsyncMock,
    ) -> None:
        """ADMIN should NOT be able to delete endpoint in different domain."""
        owner_user_id = uuid.uuid4()
        admin_user_id = uuid.uuid4()
        service_id = uuid.uuid4()

        mock_endpoint = MagicMock(
            routings=[],
            session_owner_id=owner_user_id,
            session_owner_role=UserRole.USER,
            domain="domain-a",  # Different domain
        )
        mock_get_endpoint_by_id.return_value = mock_endpoint

        action = DeleteModelServiceAction(
            service_id=service_id,
            user_data=UserData(
                user_id=admin_user_id,
                is_authorized=True,
                is_admin=True,
                is_superadmin=False,
                role="admin",
                domain_name="domain-b",  # Different from endpoint's domain
            ),
        )

        with pytest.raises(EndpointAccessForbiddenError):
            await model_serving_processors.delete_model_service.wait_for_complete(action)

    @pytest.mark.asyncio
    async def test_admin_cannot_delete_superadmin_owned_endpoint(
        self,
        model_serving_processors: ModelServingProcessors,
        mock_get_endpoint_by_id: AsyncMock,
        mock_update_endpoint_lifecycle: AsyncMock,
        mock_check_requester_access: AsyncMock,
    ) -> None:
        """ADMIN should NOT be able to delete SUPERADMIN's endpoint even in same domain."""
        superadmin_owner_id = uuid.uuid4()
        admin_user_id = uuid.uuid4()
        service_id = uuid.uuid4()

        mock_endpoint = MagicMock(
            routings=[],
            session_owner_id=superadmin_owner_id,
            session_owner_role=UserRole.SUPERADMIN,  # Owned by SUPERADMIN
            domain="default",
        )
        mock_get_endpoint_by_id.return_value = mock_endpoint

        action = DeleteModelServiceAction(
            service_id=service_id,
            user_data=UserData(
                user_id=admin_user_id,
                is_authorized=True,
                is_admin=True,
                is_superadmin=False,
                role="admin",
                domain_name="default",  # Same domain
            ),
        )

        with pytest.raises(EndpointAccessForbiddenError):
            await model_serving_processors.delete_model_service.wait_for_complete(action)

    @pytest.mark.asyncio
    async def test_superadmin_can_delete_any_endpoint(
        self,
        model_serving_processors: ModelServingProcessors,
        mock_get_endpoint_by_id: AsyncMock,
        mock_update_endpoint_lifecycle: AsyncMock,
        mock_check_requester_access: AsyncMock,
    ) -> None:
        """SUPERADMIN should be able to delete any endpoint regardless of owner."""
        owner_user_id = uuid.uuid4()
        superadmin_user_id = uuid.uuid4()
        service_id = uuid.uuid4()

        mock_endpoint = MagicMock(
            routings=[],
            session_owner_id=owner_user_id,
            session_owner_role=UserRole.USER,
            domain="other-domain",
        )
        mock_get_endpoint_by_id.return_value = mock_endpoint
        mock_update_endpoint_lifecycle.return_value = None

        action = DeleteModelServiceAction(
            service_id=service_id,
            user_data=UserData(
                user_id=superadmin_user_id,  # Different user
                is_authorized=True,
                is_admin=False,
                is_superadmin=True,
                role="superadmin",
                domain_name="different-domain",  # Different domain
            ),
        )

        result = await model_serving_processors.delete_model_service.wait_for_complete(action)
        assert result.success is True

    @pytest.mark.asyncio
    async def test_admin_can_delete_endpoint_in_same_domain(
        self,
        model_serving_processors: ModelServingProcessors,
        mock_get_endpoint_by_id: AsyncMock,
        mock_update_endpoint_lifecycle: AsyncMock,
        mock_check_requester_access: AsyncMock,
    ) -> None:
        """ADMIN should be able to delete endpoint in their domain (non-SUPERADMIN owned)."""
        owner_user_id = uuid.uuid4()
        admin_user_id = uuid.uuid4()
        service_id = uuid.uuid4()

        mock_endpoint = MagicMock(
            routings=[],
            session_owner_id=owner_user_id,
            session_owner_role=UserRole.USER,  # Not SUPERADMIN
            domain="default",
        )
        mock_get_endpoint_by_id.return_value = mock_endpoint
        mock_update_endpoint_lifecycle.return_value = None

        action = DeleteModelServiceAction(
            service_id=service_id,
            user_data=UserData(
                user_id=admin_user_id,
                is_authorized=True,
                is_admin=True,
                is_superadmin=False,
                role="admin",
                domain_name="default",  # Same domain
            ),
        )

        result = await model_serving_processors.delete_model_service.wait_for_complete(action)
        assert result.success is True
