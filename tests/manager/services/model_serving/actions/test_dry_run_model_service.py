import uuid
from typing import cast
from unittest.mock import AsyncMock, MagicMock

import pytest

from ai.backend.common.types import AccessKey, ClusterMode, RuntimeVariant
from ai.backend.manager.data.model_serving.types import ModelServicePrepareCtx, ServiceConfig
from ai.backend.manager.models.user import UserRole
from ai.backend.manager.services.model_serving.actions.dry_run_model_service import (
    DryRunModelServiceAction,
    DryRunModelServiceActionResult,
)
from ai.backend.manager.services.model_serving.processors.model_serving import (
    ModelServingProcessors,
)

from ...utils import ScenarioBase


@pytest.fixture
def mock_get_vfolder_by_id_dry_run(mocker, mock_repositories):
    mock = mocker.patch.object(
        mock_repositories.repository,
        "get_vfolder_by_id",
        new_callable=MagicMock,
    )
    mock.return_value = MagicMock(id=uuid.uuid4())
    return mock


@pytest.fixture
def mock_get_user_with_keypair(mocker, mock_repositories):
    mock = mocker.patch.object(
        mock_repositories.repository,
        "get_user_with_keypair",
        new_callable=AsyncMock,
    )
    return mock


@pytest.fixture
def mock_resolve_image_for_endpoint_creation_dry_run(mocker, mock_repositories):
    mock = mocker.patch.object(
        mock_repositories.repository,
        "resolve_image_for_endpoint_creation",
        new_callable=AsyncMock,
    )
    mock.return_value = MagicMock(image_ref="test-image:latest")
    return mock


@pytest.fixture
def mock_background_task_manager_start(mocker, mock_background_task_manager):
    mock = mocker.patch.object(
        mock_background_task_manager,
        "start",
        new_callable=AsyncMock,
    )
    return mock


class TestDryRunModelService:
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
        model_serving_processors: ModelServingProcessors,
        mock_get_vfolder_by_id_dry_run,
        mock_get_user_with_keypair,
        mock_resolve_image_for_endpoint_creation_dry_run,
        mock_background_task_manager_start,
    ):
        mock_get_user_with_keypair.return_value = MagicMock(
            uuid=scenario.input.model_service_prepare_ctx.owner_uuid,
            role=scenario.input.model_service_prepare_ctx.owner_role,
        )

        expected = cast(DryRunModelServiceActionResult, scenario.expected)
        mock_background_task_manager_start.return_value = expected.task_id

        async def dry_run_model_service(action: DryRunModelServiceAction):
            return await model_serving_processors.dry_run_model_service.wait_for_complete(action)

        await scenario.test(dry_run_model_service)
