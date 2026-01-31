from __future__ import annotations

import uuid
from collections.abc import Iterator
from typing import cast, Any
from unittest.mock import AsyncMock, MagicMock

import pytest

from ai.backend.common.bgtask.bgtask import BackgroundTaskManager
from ai.backend.common.contexts.user import with_user
from ai.backend.common.data.user.types import UserData, UserRole
from ai.backend.common.events.dispatcher import EventDispatcher
from ai.backend.common.events.hub import EventHub
from ai.backend.common.types import AccessKey, ClusterMode, RuntimeVariant
from ai.backend.manager.actions.monitors.monitor import ActionMonitor
from ai.backend.manager.clients.storage_proxy.session_manager import StorageSessionManager
from ai.backend.manager.config.provider import ManagerConfigProvider
from ai.backend.manager.data.model_serving.creator import ModelServiceCreator
from ai.backend.manager.data.model_serving.types import (
    ModelServicePrepareCtx,
    ServiceConfig,
    ServiceInfo,
)
from ai.backend.manager.models.vfolder import VFolderOwnershipType
from ai.backend.manager.repositories.model_serving.repositories import ModelServingRepositories
from ai.backend.manager.repositories.model_serving.repository import ModelServingRepository
from ai.backend.manager.services.model_serving.actions.create_model_service import (
    CreateModelServiceAction,
    CreateModelServiceActionResult,
)
from ai.backend.manager.services.model_serving.exceptions import InvalidAPIParameters
from ai.backend.manager.services.model_serving.processors.model_serving import (
    ModelServingProcessors,
)
from ai.backend.manager.services.model_serving.services.model_serving import ModelServingService
from ai.backend.manager.sokovan.deployment.deployment_controller import DeploymentController
from ai.backend.manager.sokovan.scheduling_controller import SchedulingController
from ai.backend.testutils.scenario import ScenarioBase


class TestCreateModelService:
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
        mock_deployment_controller: MagicMock,
        mock_scheduling_controller: MagicMock,
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
            deployment_controller=mock_deployment_controller,
            scheduling_controller=mock_scheduling_controller,
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
    def mock_get_vfolder_by_id(self, mocker: Any, mock_repositories: Any)-> AsyncMock:
        mock = cast(
            AsyncMock,
            mocker.patch.object(
            mock_repositories.repository,
            "get_vfolder_by_id",
            new_callable=AsyncMock,
        ),
        )
        mock.return_value = MagicMock(
            id=uuid.uuid4(),
            ownership_type=VFolderOwnershipType.USER,
        )
        return mock

    @pytest.fixture
    def mock_fetch_file_from_storage_proxy(self, mocker: Any, model_serving_service: Any)-> AsyncMock:
        mock = cast(
            AsyncMock,
            mocker.patch.object(
            model_serving_service,
            "_fetch_file_from_storage_proxy",
            new_callable=AsyncMock,
        ),
        )
        mock.return_value = None
        return mock

    @pytest.fixture
    def mock_resolve_image_for_endpoint_creation(self, mocker: Any, mock_repositories: Any)-> AsyncMock:
        mock = cast(
            AsyncMock,
            mocker.patch.object(
            mock_repositories.repository,
            "resolve_image_for_endpoint_creation",
            new_callable=AsyncMock,
        ),
        )
        mock.return_value = MagicMock(image_ref="test-image:latest")
        return mock

    @pytest.fixture
    def mock_resolve_group_id(self, mocker: Any, mock_repositories: Any)-> AsyncMock:
        mock = cast(
            AsyncMock,
            mocker.patch.object(
            mock_repositories.repository,
            "resolve_group_id",
            new_callable=AsyncMock,
        ),
        )
        mock.return_value = "test-project-id"
        return mock

    @pytest.fixture
    def mock_create_session(self, mocker: Any, mock_agent_registry: Any)-> AsyncMock:
        mock = cast(
            AsyncMock,
            mocker.patch.object(
            mock_agent_registry,
            "create_session",
            new_callable=AsyncMock,
        ),
        )
        mock.return_value = None
        return mock

    @pytest.fixture
    def mock_check_endpoint_name_uniqueness(self, mocker: Any, mock_repositories: Any)-> AsyncMock:
        mock = cast(
            AsyncMock,
            mocker.patch.object(
            mock_repositories.repository,
            "check_endpoint_name_uniqueness",
            new_callable=AsyncMock,
        ),
        )
        mock.return_value = True
        return mock

    @pytest.fixture
    def mock_create_endpoint_validated(self, mocker: Any, mock_repositories: Any)-> AsyncMock:
        return cast(
        AsyncMock,
        mocker.patch.object(
            mock_repositories.repository,
            "create_endpoint_validated",
            new_callable=AsyncMock,
        ),
    )

    @pytest.mark.parametrize(
        "scenario",
        [
            ScenarioBase.success(
                "Successful model deployment",
                CreateModelServiceAction(
                    request_user_id=uuid.UUID("00000000-0000-0000-0000-000000000001"),
                    creator=ModelServiceCreator(
                        service_name="sentiment-analyzer-v1.0",
                        replicas=2,
                        image="ai.backend/python:3.9",
                        runtime_variant=RuntimeVariant.CUSTOM,
                        architecture="x86_64",
                        group_name="group1",
                        domain_name="default",
                        cluster_size=1,
                        cluster_mode=ClusterMode.SINGLE_NODE,
                        open_to_public=False,
                        config=ServiceConfig(
                            model="sentiment-analyzer",
                            model_definition_path=None,
                            model_version=1,
                            model_mount_destination="/models",
                            extra_mounts={},
                            environ={},
                            scaling_group="default",
                            resources={"cpu": "2", "memory": "4G"},
                            resource_opts={},
                        ),
                        sudo_session_enabled=False,
                        model_service_prepare_ctx=ModelServicePrepareCtx(
                            model_id=uuid.UUID("11111111-1111-1111-1111-111111111111"),
                            model_definition_path=None,
                            requester_access_key=AccessKey("ACCESSKEY001"),
                            owner_access_key=AccessKey("ACCESSKEY001"),
                            owner_uuid=uuid.UUID("00000000-0000-0000-0000-000000000001"),
                            owner_role=UserRole.USER,
                            group_id=uuid.UUID("00000000-0000-0000-0000-000000000002"),
                            resource_policy={},
                            scaling_group="default",
                            extra_mounts=[],
                        ),
                    ),
                ),
                CreateModelServiceActionResult(
                    data=ServiceInfo(
                        endpoint_id=uuid.UUID("22222222-2222-2222-2222-222222222222"),
                        model_id=uuid.UUID("11111111-1111-1111-1111-111111111111"),
                        extra_mounts=[],
                        name="sentiment-analyzer-v1.0",
                        model_definition_path=None,
                        replicas=2,
                        desired_session_count=2,
                        active_routes=[],
                        service_endpoint=None,
                        is_public=False,
                        runtime_variant=RuntimeVariant.CUSTOM,
                    ),
                ),
            ),
            ScenarioBase.failure(
                "insufficient resources",
                CreateModelServiceAction(
                    request_user_id=uuid.UUID("00000000-0000-0000-0000-000000000001"),
                    creator=ModelServiceCreator(
                        service_name="large-model-v1.0",
                        replicas=10,
                        image="ai.backend/python:3.9",
                        runtime_variant=RuntimeVariant.CUSTOM,
                        architecture="x86_64",
                        group_name="group1",
                        domain_name="default",
                        cluster_size=1,
                        cluster_mode=ClusterMode.SINGLE_NODE,
                        open_to_public=False,
                        config=ServiceConfig(
                            model="large-model",
                            model_definition_path=None,
                            model_version=1,
                            model_mount_destination="/models",
                            extra_mounts={},
                            environ={},
                            scaling_group="default",
                            resources={"cpu": "100", "memory": "1TB"},
                            resource_opts={},
                        ),
                        sudo_session_enabled=False,
                        model_service_prepare_ctx=ModelServicePrepareCtx(
                            model_id=uuid.UUID("33333333-3333-3333-3333-333333333333"),
                            model_definition_path=None,
                            requester_access_key=AccessKey("ACCESSKEY001"),
                            owner_access_key=AccessKey("ACCESSKEY001"),
                            owner_uuid=uuid.UUID("00000000-0000-0000-0000-000000000001"),
                            owner_role=UserRole.USER,
                            group_id=uuid.UUID("00000000-0000-0000-0000-000000000002"),
                            resource_policy={},
                            scaling_group="default",
                            extra_mounts=[],
                        ),
                    ),
                ),
                Exception,  # insufficient resources
            ),
            ScenarioBase.failure(
                "duplicate model name",
                CreateModelServiceAction(
                    request_user_id=uuid.UUID("00000000-0000-0000-0000-000000000001"),
                    creator=ModelServiceCreator(
                        service_name="existing-model-v1.0",
                        replicas=1,
                        image="ai.backend/python:3.9",
                        runtime_variant=RuntimeVariant.CUSTOM,
                        architecture="x86_64",
                        group_name="group1",
                        domain_name="default",
                        cluster_size=1,
                        cluster_mode=ClusterMode.SINGLE_NODE,
                        open_to_public=False,
                        config=ServiceConfig(
                            model="existing-model",
                            model_definition_path=None,
                            model_version=1,
                            model_mount_destination="/models",
                            extra_mounts={},
                            environ={},
                            scaling_group="default",
                            resources={"cpu": "2", "memory": "4G"},
                            resource_opts={},
                        ),
                        sudo_session_enabled=False,
                        model_service_prepare_ctx=ModelServicePrepareCtx(
                            model_id=uuid.UUID("44444444-4444-4444-4444-444444444444"),
                            model_definition_path=None,
                            requester_access_key=AccessKey("ACCESSKEY001"),
                            owner_access_key=AccessKey("ACCESSKEY001"),
                            owner_uuid=uuid.UUID("00000000-0000-0000-0000-000000000001"),
                            owner_role=UserRole.USER,
                            group_id=uuid.UUID("00000000-0000-0000-0000-000000000002"),
                            resource_policy={},
                            scaling_group="default",
                            extra_mounts=[],
                        ),
                    ),
                ),
                InvalidAPIParameters,
            ),
            ScenarioBase.success(
                "public endpoint creation",
                CreateModelServiceAction(
                    request_user_id=uuid.UUID("00000000-0000-0000-0000-000000000001"),
                    creator=ModelServiceCreator(
                        service_name="public-model-v1.0",
                        replicas=3,
                        image="ai.backend/python:3.9",
                        runtime_variant=RuntimeVariant.CUSTOM,
                        architecture="x86_64",
                        group_name="group1",
                        domain_name="default",
                        cluster_size=1,
                        cluster_mode=ClusterMode.SINGLE_NODE,
                        open_to_public=True,
                        config=ServiceConfig(
                            model="public-model",
                            model_definition_path=None,
                            model_version=1,
                            model_mount_destination="/models",
                            extra_mounts={},
                            environ={},
                            scaling_group="default",
                            resources={"cpu": "2", "memory": "4G"},
                            resource_opts={},
                        ),
                        sudo_session_enabled=False,
                        model_service_prepare_ctx=ModelServicePrepareCtx(
                            model_id=uuid.UUID("55555555-5555-5555-5555-555555555555"),
                            model_definition_path=None,
                            requester_access_key=AccessKey("ACCESSKEY001"),
                            owner_access_key=AccessKey("ACCESSKEY001"),
                            owner_uuid=uuid.UUID("00000000-0000-0000-0000-000000000001"),
                            owner_role=UserRole.USER,
                            group_id=uuid.UUID("00000000-0000-0000-0000-000000000002"),
                            resource_policy={},
                            scaling_group="default",
                            extra_mounts=[],
                        ),
                    ),
                ),
                CreateModelServiceActionResult(
                    data=ServiceInfo(
                        endpoint_id=uuid.UUID("66666666-6666-6666-6666-666666666666"),
                        model_id=uuid.UUID("55555555-5555-5555-5555-555555555555"),
                        extra_mounts=[],
                        name="public-model-v1.0",
                        model_definition_path=None,
                        replicas=3,
                        desired_session_count=3,
                        active_routes=[],
                        service_endpoint=None,
                        is_public=True,
                        runtime_variant=RuntimeVariant.CUSTOM,
                    ),
                ),
            ),
        ],
    )
    @pytest.mark.asyncio
    async def test_create_model_service(
        self,
        scenario: ScenarioBase,
        model_serving_processors: ModelServingProcessors,
        mock_create_endpoint_validated: AsyncMock,
        mock_check_endpoint_name_uniqueness: AsyncMock,
        mock_create_session: AsyncMock,
    ) -> None:
        expected = cast(CreateModelServiceActionResult, scenario.expected)

        if scenario.description == "Successful model deployment":
            mock_endpoint_data = MagicMock(id=expected.data.endpoint_id)
            mock_create_endpoint_validated.return_value = mock_endpoint_data

        elif scenario.description == "insufficient resources":
            mock_create_session.side_effect = Exception("Insufficient resources")

        elif scenario.description == "duplicate model name":
            mock_check_endpoint_name_uniqueness.return_value = False

        elif scenario.description == "public endpoint creation":
            mock_endpoint_data = MagicMock(id=expected.data.endpoint_id)
            mock_create_endpoint_validated.return_value = mock_endpoint_data

        async def create_model_service(action: CreateModelServiceAction) -> None:
            return await model_serving_processors.create_model_service.wait_for_complete(action)

        await scenario.test(create_model_service)
