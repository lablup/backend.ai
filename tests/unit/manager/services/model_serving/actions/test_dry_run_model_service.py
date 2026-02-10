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
from ai.backend.common.events.hub import EventHub
from ai.backend.common.types import AccessKey, ClusterMode, ResourceSlot, RuntimeVariant
from ai.backend.manager.actions.monitors.monitor import ActionMonitor
from ai.backend.manager.clients.storage_proxy.session_manager import StorageSessionManager
from ai.backend.manager.config.provider import ManagerConfigProvider
from ai.backend.manager.data.deployment.types import (
    ExecutionSpec,
    ModelRevisionSpec,
    MountMetadata,
    ResourceSpec,
)
from ai.backend.manager.data.image.types import ImageIdentifier
from ai.backend.manager.data.model_serving.types import ModelServicePrepareCtx, ServiceConfig
from ai.backend.manager.data.vfolder.types import VFolderOwnershipType
from ai.backend.manager.repositories.model_serving.repositories import ModelServingRepositories
from ai.backend.manager.repositories.model_serving.repository import ModelServingRepository
from ai.backend.manager.services.model_serving.actions.dry_run_model_service import (
    DryRunModelServiceAction,
    DryRunModelServiceActionResult,
)
from ai.backend.manager.services.model_serving.processors.model_serving import (
    ModelServingProcessors,
)
from ai.backend.manager.services.model_serving.services.model_serving import ModelServingService
from ai.backend.manager.sokovan.deployment.deployment_controller import DeploymentController
from ai.backend.manager.sokovan.deployment.revision_generator.registry import (
    RevisionGeneratorRegistry,
)
from ai.backend.manager.sokovan.scheduling_controller import SchedulingController
from ai.backend.testutils.scenario import ScenarioBase


class TestDryRunModelService:
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
        mock = MagicMock(spec=RevisionGeneratorRegistry)
        mock_generator = MagicMock()
        mock_generator.generate_revision = AsyncMock(
            return_value=ModelRevisionSpec(
                image_identifier=ImageIdentifier(
                    canonical="ai.backend/python:3.9",
                    architecture="x86_64",
                ),
                resource_spec=ResourceSpec(
                    cluster_mode=ClusterMode.SINGLE_NODE,
                    cluster_size=1,
                    resource_slots=ResourceSlot.from_user_input({"cpu": "2", "memory": "4G"}, None),
                    resource_opts=None,
                ),
                mounts=MountMetadata(
                    model_vfolder_id=uuid.UUID("77777777-7777-7777-7777-777777777777"),
                    model_definition_path=None,
                ),
                execution=ExecutionSpec(
                    runtime_variant=RuntimeVariant.CUSTOM,
                    startup_command=None,
                    environ={},
                ),
            )
        )
        mock.get.return_value = mock_generator
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
    def mock_get_vfolder_ownership_type_dry_run(
        self, mocker: Any, mock_repositories: MagicMock
    ) -> AsyncMock:
        mock = cast(
            AsyncMock,
            mocker.patch.object(
                mock_repositories.repository,
                "get_vfolder_ownership_type",
                new_callable=AsyncMock,
            ),
        )
        mock.return_value = VFolderOwnershipType.USER
        return mock

    @pytest.fixture
    def mock_get_user_with_keypair(self, mocker: Any, mock_repositories: Any) -> AsyncMock:
        return cast(
            AsyncMock,
            mocker.patch.object(
                mock_repositories.repository,
                "get_user_with_keypair",
                new_callable=AsyncMock,
            ),
        )

    @pytest.fixture
    def mock_resolve_image_for_endpoint_creation_dry_run(
        self, mocker: Any, mock_repositories: Any
    ) -> AsyncMock:
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
    def mock_background_task_manager_start(
        self, mocker: Any, mock_background_task_manager: Any
    ) -> AsyncMock:
        return cast(
            AsyncMock,
            mocker.patch.object(
                mock_background_task_manager,
                "start",
                new_callable=AsyncMock,
            ),
        )

    @pytest.mark.parametrize(
        "scenario",
        [
            ScenarioBase.success(
                "Configuration validation success",
                DryRunModelServiceAction(
                    service_name="test-model-v1.0",
                    replicas=2,
                    image="ai.backend/python:3.9",
                    runtime_variant=RuntimeVariant.CUSTOM,
                    architecture="x86_64",
                    group_name="group1",
                    domain_name="default",
                    cluster_size=1,
                    cluster_mode=ClusterMode.SINGLE_NODE,
                    tag=None,
                    startup_command=None,
                    bootstrap_script=None,
                    callback_url=None,
                    owner_access_key=None,
                    open_to_public=False,
                    config=ServiceConfig(
                        model="test-model",
                        model_definition_path=None,
                        model_version=1,
                        model_mount_destination="/models",
                        extra_mounts={},
                        environ={},
                        scaling_group="default",
                        resources={"cpu": "2", "memory": "4G"},
                        resource_opts={},
                    ),
                    request_user_id=uuid.UUID("00000000-0000-0000-0000-000000000001"),
                    sudo_session_enabled=False,
                    model_service_prepare_ctx=ModelServicePrepareCtx(
                        model_id=uuid.UUID("77777777-7777-7777-7777-777777777777"),
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
                DryRunModelServiceActionResult(
                    task_id=uuid.UUID("aaaaaaaa-aaaa-aaaa-aaaa-aaaaaaaaaaaa"),
                ),
            ),
        ],
    )
    @pytest.mark.asyncio
    async def test_dry_run_model_service(
        self,
        scenario: ScenarioBase[DryRunModelServiceAction, DryRunModelServiceActionResult],
        user_data: UserData,
        model_serving_processors: ModelServingProcessors,
        mock_get_vfolder_ownership_type_dry_run: AsyncMock,
        mock_get_user_with_keypair: AsyncMock,
        mock_resolve_image_for_endpoint_creation_dry_run: MagicMock,
        mock_background_task_manager_start: AsyncMock,
    ) -> None:
        mock_get_user_with_keypair.return_value = MagicMock(
            uuid=scenario.input.model_service_prepare_ctx.owner_uuid,
            role=scenario.input.model_service_prepare_ctx.owner_role,
        )

        expected = cast(DryRunModelServiceActionResult, scenario.expected)
        mock_background_task_manager_start.return_value = expected.task_id

        async def dry_run_model_service(
            action: DryRunModelServiceAction,
        ) -> DryRunModelServiceActionResult:
            return await model_serving_processors.dry_run_model_service.wait_for_complete(action)

        await scenario.test(dry_run_model_service)


class TestDryRunModelServiceActionWithRevision:
    """Tests for DryRunModelServiceAction.with_revision method."""

    @pytest.fixture
    def base_service_config(self) -> ServiceConfig:
        return ServiceConfig(
            model="test-model",
            model_definition_path=None,
            model_version=1,
            model_mount_destination="/models",
            extra_mounts={},
            environ={"API_KEY": "original-value"},
            scaling_group="default",
            resources={"cpu": "1", "memory": "2G"},
            resource_opts={},
        )

    @pytest.fixture
    def base_model_service_prepare_ctx(self) -> ModelServicePrepareCtx:
        return ModelServicePrepareCtx(
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
        )

    @pytest.fixture
    def base_action(
        self,
        base_service_config: ServiceConfig,
        base_model_service_prepare_ctx: ModelServicePrepareCtx,
    ) -> DryRunModelServiceAction:
        return DryRunModelServiceAction(
            service_name="test-service",
            replicas=1,
            image="api-image:v1",
            runtime_variant=RuntimeVariant.CUSTOM,
            architecture="x86_64",
            group_name="default",
            domain_name="default",
            cluster_size=1,
            cluster_mode=ClusterMode.SINGLE_NODE,
            open_to_public=False,
            config=base_service_config,
            sudo_session_enabled=False,
            model_service_prepare_ctx=base_model_service_prepare_ctx,
            tag=None,
            startup_command=None,
            bootstrap_script=None,
            callback_url=None,
            owner_access_key=None,
            request_user_id=uuid.UUID("00000000-0000-0000-0000-000000000001"),
        )

    @pytest.fixture
    def revision_spec(self) -> ModelRevisionSpec:
        return ModelRevisionSpec(
            image_identifier=ImageIdentifier(
                canonical="service-def-image:v2",
                architecture="arm64",
            ),
            resource_spec=ResourceSpec(
                cluster_mode=ClusterMode.SINGLE_NODE,
                cluster_size=1,
                resource_slots=ResourceSlot.from_user_input({"cpu": "4", "memory": "8G"}, None),
                resource_opts=None,
            ),
            mounts=MountMetadata(
                model_vfolder_id=uuid.UUID("11111111-1111-1111-1111-111111111111"),
                model_definition_path=None,
            ),
            execution=ExecutionSpec(
                runtime_variant=RuntimeVariant.CUSTOM,
                startup_command=None,
                environ={"SERVICE_DEF_VAR": "service-def-value"},
            ),
        )

    @pytest.mark.asyncio
    async def test_with_revision_overrides(
        self,
        base_action: DryRunModelServiceAction,
        revision_spec: ModelRevisionSpec,
    ) -> None:
        result = base_action.with_revision(revision_spec)

        assert result.image == revision_spec.image_identifier.canonical
        assert result.architecture == revision_spec.image_identifier.architecture
        assert result.config.resources == dict(revision_spec.resource_spec.resource_slots)
        assert result.config.environ == revision_spec.execution.environ

    @pytest.mark.asyncio
    async def test_with_revision_returns_new_instance(
        self,
        base_action: DryRunModelServiceAction,
        revision_spec: ModelRevisionSpec,
    ) -> None:
        result = base_action.with_revision(revision_spec)

        assert result is not base_action
        assert result.config is not base_action.config

    @pytest.mark.asyncio
    async def test_with_revision_does_not_modify_original(
        self,
        base_action: DryRunModelServiceAction,
        revision_spec: ModelRevisionSpec,
    ) -> None:
        original_image = base_action.image
        original_architecture = base_action.architecture
        original_resources = base_action.config.resources
        original_environ = base_action.config.environ

        base_action.with_revision(revision_spec)

        assert base_action.image == original_image
        assert base_action.architecture == original_architecture
        assert base_action.config.resources == original_resources
        assert base_action.config.environ == original_environ

    @pytest.mark.asyncio
    async def test_with_revision_preserves_action_fields(
        self,
        base_action: DryRunModelServiceAction,
        revision_spec: ModelRevisionSpec,
    ) -> None:
        result = base_action.with_revision(revision_spec)

        assert result.service_name == base_action.service_name
        assert result.replicas == base_action.replicas
        assert result.runtime_variant == base_action.runtime_variant
        assert result.group_name == base_action.group_name
        assert result.domain_name == base_action.domain_name
        assert result.cluster_size == base_action.cluster_size
        assert result.cluster_mode == base_action.cluster_mode
        assert result.open_to_public == base_action.open_to_public
        assert result.sudo_session_enabled == base_action.sudo_session_enabled
        assert result.model_service_prepare_ctx == base_action.model_service_prepare_ctx
        assert result.tag == base_action.tag
        assert result.startup_command == base_action.startup_command
        assert result.bootstrap_script == base_action.bootstrap_script
        assert result.callback_url == base_action.callback_url
        assert result.owner_access_key == base_action.owner_access_key
        assert result.request_user_id == base_action.request_user_id

    @pytest.mark.asyncio
    async def test_with_revision_preserves_config_fields(
        self,
        base_action: DryRunModelServiceAction,
        revision_spec: ModelRevisionSpec,
    ) -> None:
        result = base_action.with_revision(revision_spec)

        assert result.config.model == base_action.config.model
        assert result.config.model_definition_path == base_action.config.model_definition_path
        assert result.config.model_version == base_action.config.model_version
        assert result.config.model_mount_destination == base_action.config.model_mount_destination
        assert result.config.extra_mounts == base_action.config.extra_mounts
        assert result.config.scaling_group == base_action.config.scaling_group
        assert result.config.resource_opts == base_action.config.resource_opts

    @pytest.fixture
    def revision_spec_with_no_environ(self) -> ModelRevisionSpec:
        return ModelRevisionSpec(
            image_identifier=ImageIdentifier(
                canonical="service-def-image:v2",
                architecture="arm64",
            ),
            resource_spec=ResourceSpec(
                cluster_mode=ClusterMode.SINGLE_NODE,
                cluster_size=1,
                resource_slots=ResourceSlot.from_user_input({"cpu": "4", "memory": "8G"}, None),
                resource_opts=None,
            ),
            mounts=MountMetadata(
                model_vfolder_id=uuid.UUID("11111111-1111-1111-1111-111111111111"),
                model_definition_path=None,
            ),
            execution=ExecutionSpec(
                runtime_variant=RuntimeVariant.CUSTOM,
                startup_command=None,
                environ=None,
            ),
        )

    @pytest.mark.asyncio
    async def test_with_revision_handles_none_environ(
        self,
        base_action: DryRunModelServiceAction,
        revision_spec_with_no_environ: ModelRevisionSpec,
    ) -> None:
        result = base_action.with_revision(revision_spec_with_no_environ)

        assert result.config.environ == revision_spec_with_no_environ.execution.environ


class TestDryRunWithServiceDefinitionOverrides:
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
    def revision_from_service_definition(self) -> ModelRevisionSpec:
        """Revision spec that would come from service definition via RevisionGenerator."""
        return ModelRevisionSpec(
            image_identifier=ImageIdentifier(
                canonical="service-def-image:v1",
                architecture="arm64",
            ),
            resource_spec=ResourceSpec(
                cluster_mode=ClusterMode.SINGLE_NODE,
                cluster_size=1,
                resource_slots=ResourceSlot.from_user_input({"cpu": "8", "memory": "16G"}, None),
                resource_opts=None,
            ),
            mounts=MountMetadata(
                model_vfolder_id=uuid.UUID("77777777-7777-7777-7777-777777777777"),
                model_definition_path=None,
            ),
            execution=ExecutionSpec(
                runtime_variant=RuntimeVariant.CUSTOM,
                startup_command=None,
                environ={"SERVICE_DEF_VAR": "from-service-definition"},
            ),
        )

    @pytest.fixture
    def mock_revision_generator_registry(
        self, revision_from_service_definition: ModelRevisionSpec
    ) -> MagicMock:
        mock = MagicMock(spec=RevisionGeneratorRegistry)
        mock_generator = MagicMock()
        mock_generator.generate_revision = AsyncMock(return_value=revision_from_service_definition)
        mock.get.return_value = mock_generator
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
    def expected_task_id(self) -> uuid.UUID:
        return uuid.UUID("aaaaaaaa-aaaa-aaaa-aaaa-aaaaaaaaaaaa")

    @pytest.fixture(autouse=True)
    def setup_repository_mocks(
        self,
        mocker: Any,
        mock_repositories: MagicMock,
        mock_background_task_manager: MagicMock,
        expected_task_id: uuid.UUID,
    ) -> dict[str, AsyncMock]:
        """Setup all repository mocks required for dry run."""
        mocks = {}

        mocks["get_vfolder_ownership_type"] = mocker.patch.object(
            mock_repositories.repository,
            "get_vfolder_ownership_type",
            new_callable=AsyncMock,
            return_value=VFolderOwnershipType.USER,
        )

        mocks["get_user_with_keypair"] = mocker.patch.object(
            mock_repositories.repository,
            "get_user_with_keypair",
            new_callable=AsyncMock,
            return_value=MagicMock(
                uuid=uuid.UUID("00000000-0000-0000-0000-000000000001"),
                role=UserRole.USER,
            ),
        )

        mocks["resolve_image_for_endpoint_creation"] = mocker.patch.object(
            mock_repositories.repository,
            "resolve_image_for_endpoint_creation",
            new_callable=AsyncMock,
            return_value=MagicMock(image_ref="test-image:latest"),
        )

        mocks["background_task_manager_start"] = mocker.patch.object(
            mock_background_task_manager,
            "start",
            new_callable=AsyncMock,
            return_value=expected_task_id,
        )

        return mocks

    @pytest.fixture
    def mock_resolve_image_for_endpoint_creation(
        self, setup_repository_mocks: dict[str, AsyncMock]
    ) -> AsyncMock:
        """Expose resolve_image mock for image override verification."""
        return setup_repository_mocks["resolve_image_for_endpoint_creation"]

    @pytest.fixture
    def action_with_api_request_values(self) -> DryRunModelServiceAction:
        """Action with values DIFFERENT from service definition."""
        return DryRunModelServiceAction(
            service_name="test-model-v1.0",
            replicas=1,
            image="api-request-image:v1",  # Different from service def
            runtime_variant=RuntimeVariant.CUSTOM,
            architecture="x86_64",  # Different from service def (arm64)
            group_name="group1",
            domain_name="default",
            cluster_size=1,
            cluster_mode=ClusterMode.SINGLE_NODE,
            tag=None,
            startup_command=None,
            bootstrap_script=None,
            callback_url=None,
            owner_access_key=None,
            open_to_public=False,
            config=ServiceConfig(
                model="test-model",
                model_definition_path=None,
                model_version=1,
                model_mount_destination="/models",
                extra_mounts={},
                environ={"API_VAR": "from-api-request"},  # Different from service def
                scaling_group="default",
                resources={"cpu": "1", "memory": "2G"},  # Different from service def
                resource_opts={},
            ),
            request_user_id=uuid.UUID("00000000-0000-0000-0000-000000000001"),
            sudo_session_enabled=False,
            model_service_prepare_ctx=ModelServicePrepareCtx(
                model_id=uuid.UUID("77777777-7777-7777-7777-777777777777"),
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
        )

    @pytest.mark.asyncio
    async def test_service_definition_overrides_applied(
        self,
        model_serving_processors: ModelServingProcessors,
        action_with_api_request_values: DryRunModelServiceAction,
        revision_from_service_definition: ModelRevisionSpec,
        expected_task_id: uuid.UUID,
        mock_scheduling_controller: MagicMock,
        mock_resolve_image_for_endpoint_creation: AsyncMock,
    ) -> None:
        """Verify dry run applies service definition overrides from RevisionGenerator."""
        result = await model_serving_processors.dry_run_model_service.wait_for_complete(
            action_with_api_request_values
        )

        # Verify image resolution uses revision values (not API request values)
        mock_resolve_image_for_endpoint_creation.assert_called_once()
        image_identifiers = mock_resolve_image_for_endpoint_creation.call_args[0][0]
        assert (
            image_identifiers[0].canonical
            == revision_from_service_definition.image_identifier.canonical
        )
        assert (
            image_identifiers[0].architecture
            == revision_from_service_definition.image_identifier.architecture
        )

        # Verify session spec uses revision values (not API request values)
        mock_scheduling_controller.enqueue_session.assert_called_once()
        session_spec = mock_scheduling_controller.enqueue_session.call_args[0][0]
        kernel_creation_config = session_spec.kernel_specs[0]["creation_config"]

        expected_resources = dict(revision_from_service_definition.resource_spec.resource_slots)
        assert kernel_creation_config["resources"] == expected_resources

        expected_environ = revision_from_service_definition.execution.environ
        assert kernel_creation_config["environ"] == expected_environ

        # Verify successful completion
        assert result.task_id == expected_task_id
