"""
Mock-based unit tests for ModelServingService actions:
ModifyEndpoint, ForceSync, DeleteRoute.
"""

from __future__ import annotations

import uuid
from collections.abc import Iterator
from typing import Any, cast
from unittest.mock import AsyncMock, MagicMock

import pytest

from ai.backend.common.bgtask.bgtask import BackgroundTaskManager
from ai.backend.common.contexts.user import with_user
from ai.backend.common.data.user.types import UserData, UserRole
from ai.backend.common.events.dispatcher import EventDispatcher
from ai.backend.common.events.event_types.kernel.types import KernelLifecycleEventReason
from ai.backend.common.events.hub import EventHub
from ai.backend.manager.actions.monitors.monitor import ActionMonitor
from ai.backend.manager.clients.storage_proxy.session_manager import StorageSessionManager
from ai.backend.manager.config.provider import ManagerConfigProvider
from ai.backend.manager.data.model_serving.types import MutationResult
from ai.backend.manager.errors.service import (
    EndpointAccessForbiddenError,
    ModelServiceNotFound,
    RouteNotFound,
)
from ai.backend.manager.models.routing import RouteStatus
from ai.backend.manager.repositories.model_serving.repositories import ModelServingRepositories
from ai.backend.manager.repositories.model_serving.repository import ModelServingRepository
from ai.backend.manager.repositories.model_serving.updaters import EndpointUpdaterSpec
from ai.backend.manager.services.model_serving.actions.delete_route import (
    DeleteRouteAction,
)
from ai.backend.manager.services.model_serving.actions.force_sync import (
    ForceSyncAction,
)
from ai.backend.manager.services.model_serving.actions.modify_endpoint import (
    ModifyEndpointAction,
)
from ai.backend.manager.services.model_serving.exceptions import InvalidAPIParameters
from ai.backend.manager.services.model_serving.processors.model_serving import (
    ModelServingProcessors,
)
from ai.backend.manager.services.model_serving.services.model_serving import ModelServingService
from ai.backend.manager.sokovan.deployment.deployment_controller import DeploymentController
from ai.backend.manager.sokovan.deployment.revision_generator.registry import (
    RevisionGeneratorRegistry,
)
from ai.backend.manager.sokovan.deployment.types import DeploymentLifecycleType
from ai.backend.manager.sokovan.scheduling_controller import SchedulingController
from ai.backend.manager.types import OptionalState


class ModelServingCRUDBaseFixtures:
    """Shared fixtures for ModelServing CRUD action tests."""

    @pytest.fixture
    def user_data(self) -> UserData:
        return UserData(
            user_id=uuid.UUID("00000000-0000-0000-0000-000000000001"),
            is_authorized=True,
            is_admin=False,
            is_superadmin=False,
            role=UserRole.USER,
            domain_name="default",
        )

    @pytest.fixture(autouse=True)
    def set_user_context(self, user_data: UserData) -> Iterator[None]:
        with with_user(user_data):
            yield

    @pytest.fixture
    def mock_storage_manager(self) -> MagicMock:
        return MagicMock(spec=StorageSessionManager)

    @pytest.fixture
    def mock_action_monitor(self) -> MagicMock:
        return MagicMock(spec=ActionMonitor)

    @pytest.fixture
    def mock_event_dispatcher(self) -> MagicMock:
        mock = MagicMock(spec=EventDispatcher)
        mock.dispatch = AsyncMock()
        return mock

    @pytest.fixture
    def mock_agent_registry(self) -> MagicMock:
        return MagicMock()

    @pytest.fixture
    def mock_config_provider(self) -> MagicMock:
        return MagicMock(spec=ManagerConfigProvider)

    @pytest.fixture
    def mock_repositories(self) -> MagicMock:
        mock = MagicMock(spec=ModelServingRepositories)
        mock.repository = MagicMock(spec=ModelServingRepository)
        return mock

    @pytest.fixture
    def mock_background_task_manager(self) -> MagicMock:
        return MagicMock(spec=BackgroundTaskManager)

    @pytest.fixture
    def mock_valkey_live(self) -> MagicMock:
        mock = MagicMock()
        mock.store_live_data = AsyncMock()
        mock.get_live_data = AsyncMock()
        mock.delete_live_data = AsyncMock()
        return mock

    @pytest.fixture
    def mock_deployment_controller(self) -> MagicMock:
        mock = MagicMock(spec=DeploymentController)
        mock.mark_lifecycle_needed = AsyncMock()
        return mock

    @pytest.fixture
    def mock_deployment_repository(self) -> MagicMock:
        mock = MagicMock()
        mock.get_default_architecture_from_scaling_group = AsyncMock(return_value=None)
        return mock

    @pytest.fixture
    def mock_event_hub(self) -> MagicMock:
        mock = MagicMock(spec=EventHub)
        mock.register_event_propagator = MagicMock()
        mock.unregister_event_propagator = MagicMock()
        return mock

    @pytest.fixture
    def mock_scheduling_controller(self) -> MagicMock:
        mock = MagicMock(spec=SchedulingController)
        mock.enqueue_session = AsyncMock()
        mock.mark_sessions_for_termination = AsyncMock()
        return mock

    @pytest.fixture
    def mock_revision_generator_registry(self) -> MagicMock:
        return MagicMock(spec=RevisionGeneratorRegistry)

    @pytest.fixture
    def model_serving_service(
        self,
        mock_storage_manager: MagicMock,
        mock_event_dispatcher: MagicMock,
        mock_event_hub: MagicMock,
        mock_agent_registry: MagicMock,
        mock_background_task_manager: MagicMock,
        mock_config_provider: MagicMock,
        mock_valkey_live: MagicMock,
        mock_repositories: MagicMock,
        mock_deployment_repository: MagicMock,
        mock_deployment_controller: MagicMock,
        mock_scheduling_controller: MagicMock,
        mock_revision_generator_registry: MagicMock,
    ) -> ModelServingService:
        return ModelServingService(
            agent_registry=mock_agent_registry,
            background_task_manager=mock_background_task_manager,
            event_dispatcher=mock_event_dispatcher,
            event_hub=mock_event_hub,
            storage_manager=mock_storage_manager,
            config_provider=mock_config_provider,
            valkey_live=mock_valkey_live,
            repository=mock_repositories.repository,
            deployment_repository=mock_deployment_repository,
            deployment_controller=mock_deployment_controller,
            scheduling_controller=mock_scheduling_controller,
            revision_generator_registry=mock_revision_generator_registry,
        )

    @pytest.fixture
    def model_serving_processors(
        self,
        mock_action_monitor: MagicMock,
        model_serving_service: ModelServingService,
    ) -> ModelServingProcessors:
        return ModelServingProcessors(
            service=model_serving_service,
            action_monitors=[mock_action_monitor],
        )

    @pytest.fixture
    def mock_check_user_access(self, mocker: Any, model_serving_service: Any) -> AsyncMock:
        mock = cast(
            AsyncMock,
            mocker.patch.object(
                model_serving_service,
                "check_user_access",
                new_callable=AsyncMock,
            ),
        )
        mock.return_value = None
        return mock

    @pytest.fixture
    def service_id(self) -> uuid.UUID:
        return uuid.UUID("aaaaaaaa-bbbb-cccc-dddd-eeeeeeeeeeee")

    @pytest.fixture
    def route_id(self) -> uuid.UUID:
        return uuid.UUID("11111111-2222-3333-4444-555555555555")

    @pytest.fixture
    def endpoint_id(self) -> uuid.UUID:
        return uuid.UUID("ffffffff-eeee-dddd-cccc-bbbbbbbbbbbb")


class TestModifyEndpoint(ModelServingCRUDBaseFixtures):
    """Tests for ModelServingService.modify_endpoint"""

    @pytest.fixture
    def mock_modify_endpoint(self, mocker: Any, mock_repositories: Any) -> AsyncMock:
        return cast(
            AsyncMock,
            mocker.patch.object(
                mock_repositories.repository,
                "modify_endpoint",
                new_callable=AsyncMock,
            ),
        )

    def _make_updater_spec(self, *, replicas: int | None = None) -> MagicMock:
        spec = MagicMock(spec=EndpointUpdaterSpec)
        if replicas is not None:
            spec.replicas = OptionalState.update(replicas)
            spec.replica_count_modified.return_value = True
        else:
            spec.replicas = OptionalState[int].nop()
            spec.replica_count_modified.return_value = False
        return spec

    async def test_replica_count_change_marks_check_replica(
        self,
        model_serving_processors: ModelServingProcessors,
        mock_modify_endpoint: AsyncMock,
        mock_deployment_controller: MagicMock,
        endpoint_id: uuid.UUID,
    ) -> None:
        """replica_count change (2->5) returns success=true with CHECK_REPLICA marking."""
        updater_spec = self._make_updater_spec(replicas=5)
        mock_updater = MagicMock()
        mock_updater.spec = updater_spec

        mock_endpoint_data = MagicMock()
        mock_endpoint_data.id = endpoint_id
        mock_modify_endpoint.return_value = MutationResult(
            success=True, message="ok", data=mock_endpoint_data
        )

        action = ModifyEndpointAction(endpoint_id=endpoint_id, updater=mock_updater)
        result = await model_serving_processors.modify_endpoint.wait_for_complete(action)

        assert result.success is True
        assert result.data == mock_endpoint_data
        mock_deployment_controller.mark_lifecycle_needed.assert_called_once_with(
            DeploymentLifecycleType.CHECK_REPLICA
        )

    async def test_no_replica_change_no_marking(
        self,
        model_serving_processors: ModelServingProcessors,
        mock_modify_endpoint: AsyncMock,
        mock_deployment_controller: MagicMock,
        endpoint_id: uuid.UUID,
    ) -> None:
        """No replica change returns success without CHECK_REPLICA marking."""
        updater_spec = self._make_updater_spec(replicas=None)
        mock_updater = MagicMock()
        mock_updater.spec = updater_spec

        mock_endpoint_data = MagicMock()
        mock_endpoint_data.id = endpoint_id
        mock_modify_endpoint.return_value = MutationResult(
            success=True, message="ok", data=mock_endpoint_data
        )

        action = ModifyEndpointAction(endpoint_id=endpoint_id, updater=mock_updater)
        result = await model_serving_processors.modify_endpoint.wait_for_complete(action)

        assert result.success is True
        mock_deployment_controller.mark_lifecycle_needed.assert_not_called()

    async def test_non_existent_endpoint_raises(
        self,
        model_serving_processors: ModelServingProcessors,
        mock_modify_endpoint: AsyncMock,
        endpoint_id: uuid.UUID,
    ) -> None:
        """Non-existent endpoint raises error from repository."""
        updater_spec = self._make_updater_spec(replicas=5)
        mock_updater = MagicMock()
        mock_updater.spec = updater_spec
        mock_modify_endpoint.side_effect = Exception("Endpoint not found")

        action = ModifyEndpointAction(endpoint_id=endpoint_id, updater=mock_updater)
        with pytest.raises(Exception, match="Endpoint not found"):
            await model_serving_processors.modify_endpoint.wait_for_complete(action)


class TestForceSync(ModelServingCRUDBaseFixtures):
    """Tests for ModelServingService.force_sync_with_app_proxy"""

    @pytest.fixture
    def mock_get_endpoint_access_validation_data(
        self, mocker: Any, mock_repositories: Any
    ) -> AsyncMock:
        return cast(
            AsyncMock,
            mocker.patch.object(
                mock_repositories.repository,
                "get_endpoint_access_validation_data",
                new_callable=AsyncMock,
            ),
        )

    @pytest.fixture
    def mock_notify_appproxy(self, mocker: Any, mock_agent_registry: Any) -> AsyncMock:
        mock = cast(
            AsyncMock,
            mocker.patch.object(
                mock_agent_registry,
                "notify_endpoint_route_update_to_appproxy",
                new_callable=AsyncMock,
            ),
        )
        mock.return_value = None
        return mock

    def _make_validation_data(self, user_data: UserData) -> MagicMock:
        return MagicMock(
            session_owner_id=user_data.user_id,
            session_owner_role=UserRole(user_data.role),
            domain=user_data.domain_name,
        )

    async def test_valid_service_returns_success(
        self,
        model_serving_processors: ModelServingProcessors,
        mock_check_user_access: AsyncMock,
        mock_get_endpoint_access_validation_data: AsyncMock,
        mock_notify_appproxy: AsyncMock,
        user_data: UserData,
        service_id: uuid.UUID,
    ) -> None:
        """Valid service_id returns success=true with notify called once."""
        mock_get_endpoint_access_validation_data.return_value = self._make_validation_data(
            user_data
        )

        action = ForceSyncAction(service_id=service_id)
        result = await model_serving_processors.force_sync.wait_for_complete(action)

        assert result.success is True
        mock_notify_appproxy.assert_called_once_with(service_id)

    async def test_non_existent_service_raises(
        self,
        model_serving_processors: ModelServingProcessors,
        mock_check_user_access: AsyncMock,
        mock_get_endpoint_access_validation_data: AsyncMock,
        service_id: uuid.UUID,
    ) -> None:
        """Non-existent service raises ModelServiceNotFound."""
        mock_get_endpoint_access_validation_data.return_value = None

        action = ForceSyncAction(service_id=service_id)
        with pytest.raises(ModelServiceNotFound):
            await model_serving_processors.force_sync.wait_for_complete(action)

    async def test_non_owner_access_raises(
        self,
        model_serving_processors: ModelServingProcessors,
        mock_check_user_access: AsyncMock,
        mock_get_endpoint_access_validation_data: AsyncMock,
        service_id: uuid.UUID,
    ) -> None:
        """Non-owner access raises EndpointAccessForbiddenError."""
        mock_get_endpoint_access_validation_data.return_value = MagicMock(
            session_owner_id=uuid.UUID("99999999-9999-9999-9999-999999999999"),
            session_owner_role=UserRole.USER,
            domain="other-domain",
        )

        action = ForceSyncAction(service_id=service_id)
        with pytest.raises(EndpointAccessForbiddenError):
            await model_serving_processors.force_sync.wait_for_complete(action)


class TestDeleteRoute(ModelServingCRUDBaseFixtures):
    """Tests for ModelServingService.delete_route"""

    @pytest.fixture
    def mock_get_endpoint_access_validation_data(
        self, mocker: Any, mock_repositories: Any
    ) -> AsyncMock:
        return cast(
            AsyncMock,
            mocker.patch.object(
                mock_repositories.repository,
                "get_endpoint_access_validation_data",
                new_callable=AsyncMock,
            ),
        )

    @pytest.fixture
    def mock_get_route_by_id(self, mocker: Any, mock_repositories: Any) -> AsyncMock:
        return cast(
            AsyncMock,
            mocker.patch.object(
                mock_repositories.repository,
                "get_route_by_id",
                new_callable=AsyncMock,
            ),
        )

    @pytest.fixture
    def mock_get_route_with_session(self, mocker: Any, mock_repositories: Any) -> AsyncMock:
        return cast(
            AsyncMock,
            mocker.patch.object(
                mock_repositories.repository,
                "get_route_with_session",
                new_callable=AsyncMock,
            ),
        )

    @pytest.fixture
    def mock_destroy_session(self, mocker: Any, mock_agent_registry: Any) -> AsyncMock:
        return cast(
            AsyncMock,
            mocker.patch.object(
                mock_agent_registry,
                "destroy_session",
                new_callable=AsyncMock,
            ),
        )

    @pytest.fixture
    def mock_decrease_endpoint_replicas(self, mocker: Any, mock_repositories: Any) -> AsyncMock:
        return cast(
            AsyncMock,
            mocker.patch.object(
                mock_repositories.repository,
                "decrease_endpoint_replicas",
                new_callable=AsyncMock,
            ),
        )

    def _make_validation_data(self, user_data: UserData) -> MagicMock:
        return MagicMock(
            session_owner_id=user_data.user_id,
            session_owner_role=UserRole(user_data.role),
            domain=user_data.domain_name,
        )

    async def test_healthy_route_deletion_success(
        self,
        model_serving_processors: ModelServingProcessors,
        mock_check_user_access: AsyncMock,
        mock_get_endpoint_access_validation_data: AsyncMock,
        mock_get_route_by_id: AsyncMock,
        mock_get_route_with_session: AsyncMock,
        mock_destroy_session: AsyncMock,
        mock_decrease_endpoint_replicas: AsyncMock,
        user_data: UserData,
        service_id: uuid.UUID,
        route_id: uuid.UUID,
    ) -> None:
        """HEALTHY route deletion returns success=true with destroy_session + decrease_replicas."""
        mock_get_endpoint_access_validation_data.return_value = self._make_validation_data(
            user_data
        )
        mock_route_data = MagicMock(status=RouteStatus.HEALTHY)
        mock_get_route_by_id.return_value = mock_route_data

        mock_session_row = MagicMock()
        mock_route_row = MagicMock(session_row=mock_session_row)
        mock_get_route_with_session.return_value = mock_route_row

        action = DeleteRouteAction(service_id=service_id, route_id=route_id)
        result = await model_serving_processors.delete_route.wait_for_complete(action)

        assert result.success is True
        mock_destroy_session.assert_called_once_with(
            mock_session_row,
            forced=False,
            reason=KernelLifecycleEventReason.SERVICE_SCALED_DOWN,
        )
        mock_decrease_endpoint_replicas.assert_called_once_with(service_id)

    async def test_provisioning_state_raises(
        self,
        model_serving_processors: ModelServingProcessors,
        mock_check_user_access: AsyncMock,
        mock_get_endpoint_access_validation_data: AsyncMock,
        mock_get_route_by_id: AsyncMock,
        user_data: UserData,
        service_id: uuid.UUID,
        route_id: uuid.UUID,
    ) -> None:
        """PROVISIONING state raises InvalidAPIParameters."""
        mock_get_endpoint_access_validation_data.return_value = self._make_validation_data(
            user_data
        )
        mock_get_route_by_id.return_value = MagicMock(status=RouteStatus.PROVISIONING)

        action = DeleteRouteAction(service_id=service_id, route_id=route_id)
        with pytest.raises(InvalidAPIParameters, match="PROVISIONING"):
            await model_serving_processors.delete_route.wait_for_complete(action)

    async def test_sessionless_route_deletes_without_session_destruction(
        self,
        model_serving_processors: ModelServingProcessors,
        mock_check_user_access: AsyncMock,
        mock_get_endpoint_access_validation_data: AsyncMock,
        mock_get_route_by_id: AsyncMock,
        mock_get_route_with_session: AsyncMock,
        mock_destroy_session: AsyncMock,
        mock_decrease_endpoint_replicas: AsyncMock,
        user_data: UserData,
        service_id: uuid.UUID,
        route_id: uuid.UUID,
    ) -> None:
        """Sessionless route deletes without session destruction call."""
        mock_get_endpoint_access_validation_data.return_value = self._make_validation_data(
            user_data
        )
        mock_get_route_by_id.return_value = MagicMock(status=RouteStatus.HEALTHY)
        mock_get_route_with_session.return_value = MagicMock(session_row=None)

        action = DeleteRouteAction(service_id=service_id, route_id=route_id)
        result = await model_serving_processors.delete_route.wait_for_complete(action)

        assert result.success is True
        mock_destroy_session.assert_not_called()
        mock_decrease_endpoint_replicas.assert_called_once_with(service_id)

    async def test_non_existent_route_raises(
        self,
        model_serving_processors: ModelServingProcessors,
        mock_check_user_access: AsyncMock,
        mock_get_endpoint_access_validation_data: AsyncMock,
        mock_get_route_by_id: AsyncMock,
        user_data: UserData,
        service_id: uuid.UUID,
        route_id: uuid.UUID,
    ) -> None:
        """Non-existent route raises RouteNotFound."""
        mock_get_endpoint_access_validation_data.return_value = self._make_validation_data(
            user_data
        )
        mock_get_route_by_id.return_value = None

        action = DeleteRouteAction(service_id=service_id, route_id=route_id)
        with pytest.raises(RouteNotFound):
            await model_serving_processors.delete_route.wait_for_complete(action)

    async def test_non_owner_access_raises(
        self,
        model_serving_processors: ModelServingProcessors,
        mock_check_user_access: AsyncMock,
        mock_get_endpoint_access_validation_data: AsyncMock,
        service_id: uuid.UUID,
        route_id: uuid.UUID,
    ) -> None:
        """Non-owner access raises EndpointAccessForbiddenError."""
        mock_get_endpoint_access_validation_data.return_value = MagicMock(
            session_owner_id=uuid.UUID("99999999-9999-9999-9999-999999999999"),
            session_owner_role=UserRole.USER,
            domain="other-domain",
        )

        action = DeleteRouteAction(service_id=service_id, route_id=route_id)
        with pytest.raises(EndpointAccessForbiddenError):
            await model_serving_processors.delete_route.wait_for_complete(action)
