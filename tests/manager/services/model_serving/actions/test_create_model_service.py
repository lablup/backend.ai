import uuid
from typing import cast
from unittest.mock import AsyncMock, MagicMock

import pytest

from ai.backend.common.types import AccessKey, ClusterMode, RuntimeVariant
from ai.backend.manager.data.model_serving.creator import ModelServiceCreator
from ai.backend.manager.data.model_serving.types import (
    ModelServicePrepareCtx,
    ServiceConfig,
    ServiceInfo,
)
from ai.backend.manager.models.user import UserRole
from ai.backend.manager.models.vfolder import VFolderOwnershipType
from ai.backend.manager.services.model_serving.actions.create_model_service import (
    CreateModelServiceAction,
    CreateModelServiceActionResult,
)
from ai.backend.manager.services.model_serving.exceptions import InvalidAPIParameters
from ai.backend.manager.services.model_serving.processors.model_serving import (
    ModelServingProcessors,
)

from ...utils import ScenarioBase


@pytest.fixture
def mock_get_vfolder_by_id(mocker, mock_repositories):
    mock = mocker.patch.object(
        mock_repositories.repository,
        "get_vfolder_by_id",
        new_callable=AsyncMock,
    )
    mock.return_value = MagicMock(
        id=uuid.uuid4(),
        ownership_type=VFolderOwnershipType.USER,
    )
    return mock


@pytest.fixture
def mock_fetch_file_from_storage_proxy(mocker, model_serving_service):
    mock = mocker.patch.object(
        model_serving_service,
        "_fetch_file_from_storage_proxy",
        new_callable=AsyncMock,
    )
    mock.return_value = None
    return mock


@pytest.fixture
def mock_resolve_image_for_endpoint_creation(mocker, mock_repositories):
    mock = mocker.patch.object(
        mock_repositories.repository,
        "resolve_image_for_endpoint_creation",
        new_callable=AsyncMock,
    )
    mock.return_value = MagicMock(image_ref="test-image:latest")
    return mock


@pytest.fixture
def mock_resolve_group_id(mocker, mock_repositories):
    mock = mocker.patch.object(
        mock_repositories.repository,
        "resolve_group_id",
        new_callable=AsyncMock,
    )
    mock.return_value = "test-project-id"
    return mock


@pytest.fixture
def mock_create_session(mocker, mock_agent_registry):
    mock = mocker.patch.object(
        mock_agent_registry,
        "create_session",
        new_callable=AsyncMock,
    )
    mock.return_value = None
    return mock


@pytest.fixture
def mock_check_endpoint_name_uniqueness(mocker, mock_repositories):
    mock = mocker.patch.object(
        mock_repositories.repository,
        "check_endpoint_name_uniqueness",
        new_callable=AsyncMock,
    )
    mock.return_value = True
    return mock


@pytest.fixture
def mock_create_endpoint_validated(mocker, mock_repositories):
    mock = mocker.patch.object(
        mock_repositories.repository,
        "create_endpoint_validated",
        new_callable=AsyncMock,
    )
    return mock


class TestCreateModelService:
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
        scenario: ScenarioBase[CreateModelServiceAction, CreateModelServiceActionResult],
        model_serving_processors: ModelServingProcessors,
        mock_get_vfolder_by_id,
        mock_fetch_file_from_storage_proxy,
        mock_resolve_image_for_endpoint_creation,
        mock_resolve_group_id,
        mock_create_session,
        mock_check_endpoint_name_uniqueness,
        mock_create_endpoint_validated,
    ):
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

        async def create_model_service(action: CreateModelServiceAction):
            return await model_serving_processors.create_model_service.wait_for_complete(action)

        await scenario.test(create_model_service)
