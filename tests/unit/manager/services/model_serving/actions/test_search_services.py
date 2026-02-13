from __future__ import annotations

import uuid
from collections.abc import Iterator
from typing import Any, cast
from unittest.mock import AsyncMock, MagicMock

import pytest
from pydantic import HttpUrl

from ai.backend.common.bgtask.bgtask import BackgroundTaskManager
from ai.backend.common.contexts.user import with_user
from ai.backend.common.data.user.types import UserData, UserRole
from ai.backend.common.dto.manager.query import StringFilter
from ai.backend.common.events.dispatcher import EventDispatcher
from ai.backend.common.events.hub import EventHub
from ai.backend.common.types import ResourceSlot
from ai.backend.manager.actions.monitors.monitor import ActionMonitor
from ai.backend.manager.api.service import ServiceFilterModel
from ai.backend.manager.clients.storage_proxy.session_manager import StorageSessionManager
from ai.backend.manager.config.provider import ManagerConfigProvider
from ai.backend.manager.data.model_serving.types import (
    ServiceSearchItem,
    ServiceSearchResult,
)
from ai.backend.manager.repositories.model_serving.repositories import ModelServingRepositories
from ai.backend.manager.repositories.model_serving.repository import ModelServingRepository
from ai.backend.manager.services.model_serving.actions.search_services import (
    SearchServicesAction,
    SearchServicesActionResult,
)
from ai.backend.manager.services.model_serving.adapter import ServiceSearchAdapter
from ai.backend.manager.services.model_serving.processors.model_serving import (
    ModelServingProcessors,
)
from ai.backend.manager.services.model_serving.services.model_serving import ModelServingService
from ai.backend.manager.sokovan.deployment.deployment_controller import DeploymentController
from ai.backend.manager.sokovan.deployment.revision_generator.registry import (
    RevisionGeneratorRegistry,
)
from ai.backend.manager.sokovan.scheduling_controller import SchedulingController


class TestSearchServices:
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
    def mock_search_services_paginated(
        self, mocker: Any, mock_repositories: MagicMock
    ) -> AsyncMock:
        return cast(
            AsyncMock,
            mocker.patch.object(
                mock_repositories.repository,
                "search_services_paginated",
                new_callable=AsyncMock,
            ),
        )

    @pytest.mark.asyncio
    async def test_empty_result(
        self,
        model_serving_processors: ModelServingProcessors,
        mock_search_services_paginated: AsyncMock,
    ) -> None:
        """No services exist — verify empty items array with total count of 0."""
        mock_search_services_paginated.return_value = ServiceSearchResult(
            items=[],
            total_count=0,
            has_next_page=False,
            has_previous_page=False,
        )

        action = SearchServicesAction(
            session_owner_id=uuid.UUID("00000000-0000-0000-0000-000000000001"),
            conditions=[],
            offset=0,
            limit=20,
        )
        result: SearchServicesActionResult = (
            await model_serving_processors.search_services.wait_for_complete(action)
        )

        assert result.items == []
        assert result.total_count == 0
        assert result.offset == 0
        assert result.limit == 20

    @pytest.mark.asyncio
    async def test_services_with_active_routes(
        self,
        model_serving_processors: ModelServingProcessors,
        mock_search_services_paginated: AsyncMock,
    ) -> None:
        """Services exist with active routes — verify active_route_count and resource_slots."""
        endpoint_id = uuid.UUID("88888888-9999-aaaa-bbbb-cccccccccccc")
        resource_slots = ResourceSlot({"cpu": "4", "mem": "32g"})

        mock_search_services_paginated.return_value = ServiceSearchResult(
            items=[
                ServiceSearchItem(
                    id=endpoint_id,
                    name="my-inference-service",
                    replicas=2,
                    active_route_count=2,
                    service_endpoint=HttpUrl("https://api.example.com/v1/my-service"),
                    open_to_public=False,
                    resource_slots=resource_slots,
                    resource_group="nvidia-H100",
                    routings=None,
                ),
            ],
            total_count=1,
            has_next_page=False,
            has_previous_page=False,
        )

        action = SearchServicesAction(
            session_owner_id=uuid.UUID("00000000-0000-0000-0000-000000000001"),
            conditions=[],
            offset=0,
            limit=20,
        )
        result: SearchServicesActionResult = (
            await model_serving_processors.search_services.wait_for_complete(action)
        )

        assert len(result.items) == 1
        assert result.items[0].id == endpoint_id
        assert result.items[0].name == "my-inference-service"
        assert result.items[0].replicas == 2
        assert result.items[0].active_route_count == 2
        assert result.items[0].resource_slots == resource_slots
        assert result.items[0].open_to_public is False
        assert result.total_count == 1

    @pytest.mark.asyncio
    async def test_service_with_null_endpoint(
        self,
        model_serving_processors: ModelServingProcessors,
        mock_search_services_paginated: AsyncMock,
    ) -> None:
        """Service with no public URL — verify service_endpoint is None."""
        endpoint_id = uuid.UUID("aaaaaaaa-bbbb-cccc-dddd-eeeeeeeeeeee")

        mock_search_services_paginated.return_value = ServiceSearchResult(
            items=[
                ServiceSearchItem(
                    id=endpoint_id,
                    name="no-url-service",
                    replicas=1,
                    active_route_count=0,
                    service_endpoint=None,
                    open_to_public=True,
                    resource_slots=ResourceSlot({"cpu": "2"}),
                    resource_group="default",
                    routings=None,
                ),
            ],
            total_count=1,
            has_next_page=False,
            has_previous_page=False,
        )

        action = SearchServicesAction(
            session_owner_id=uuid.UUID("00000000-0000-0000-0000-000000000001"),
            conditions=[],
            offset=0,
            limit=20,
        )
        result: SearchServicesActionResult = (
            await model_serving_processors.search_services.wait_for_complete(action)
        )

        assert len(result.items) == 1
        assert result.items[0].service_endpoint is None
        assert result.items[0].active_route_count == 0
        assert result.items[0].open_to_public is True

    @pytest.mark.asyncio
    async def test_pagination_metadata(
        self,
        model_serving_processors: ModelServingProcessors,
        mock_search_services_paginated: AsyncMock,
    ) -> None:
        """Paginate through a large service list — verify correct total count and offset."""
        items = [
            ServiceSearchItem(
                id=uuid.uuid4(),
                name=f"service-{i}",
                replicas=1,
                active_route_count=0,
                service_endpoint=None,
                open_to_public=False,
                resource_slots=ResourceSlot({"cpu": "1"}),
                resource_group="default",
                routings=None,
            )
            for i in range(5)
        ]

        mock_search_services_paginated.return_value = ServiceSearchResult(
            items=items,
            total_count=15,
            has_next_page=True,
            has_previous_page=True,
        )

        action = SearchServicesAction(
            session_owner_id=uuid.UUID("00000000-0000-0000-0000-000000000001"),
            conditions=[],
            offset=5,
            limit=5,
        )
        result: SearchServicesActionResult = (
            await model_serving_processors.search_services.wait_for_complete(action)
        )

        assert len(result.items) == 5
        assert result.total_count == 15
        assert result.offset == 5
        assert result.limit == 5

    @pytest.mark.asyncio
    async def test_name_filter(
        self,
        model_serving_processors: ModelServingProcessors,
        mock_search_services_paginated: AsyncMock,
    ) -> None:
        """Filtered by name — verify repository is called with correct querier."""
        mock_search_services_paginated.return_value = ServiceSearchResult(
            items=[
                ServiceSearchItem(
                    id=uuid.UUID("11111111-2222-3333-4444-555555555555"),
                    name="target-service",
                    replicas=3,
                    active_route_count=1,
                    service_endpoint=HttpUrl("https://api.example.com/v1/target"),
                    open_to_public=False,
                    resource_slots=ResourceSlot({"cpu": "4", "cuda.shares": "2.5"}),
                    resource_group="gpu-cluster",
                    routings=None,
                ),
            ],
            total_count=1,
            has_next_page=False,
            has_previous_page=False,
        )

        adapter = ServiceSearchAdapter()
        name_filter = StringFilter(equals="target-service")
        conditions = adapter.convert_filter(ServiceFilterModel(name=name_filter))

        action = SearchServicesAction(
            session_owner_id=uuid.UUID("00000000-0000-0000-0000-000000000001"),
            conditions=conditions,
            offset=0,
            limit=20,
        )
        result: SearchServicesActionResult = (
            await model_serving_processors.search_services.wait_for_complete(action)
        )

        assert len(result.items) == 1
        assert result.items[0].name == "target-service"
        assert result.total_count == 1

        # Verify repository was called with a querier that has conditions
        call_args = mock_search_services_paginated.call_args
        querier = call_args[0][1]  # second positional arg
        assert len(querier.conditions) == 1  # name filter condition
