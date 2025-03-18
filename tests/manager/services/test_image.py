import uuid

import pytest

from ai.backend.manager.api.context import RootContext
from ai.backend.manager.models.image import ImageRow
from ai.backend.manager.models.user import UserRole
from ai.backend.manager.server import (
    agent_registry_ctx,
    background_task_ctx,
    database_ctx,
    event_dispatcher_ctx,
    hook_plugin_ctx,
    monitoring_ctx,
    network_plugin_ctx,
    processors_ctx,
    redis_ctx,
    services_ctx,
    shared_config_ctx,
    storage_manager_ctx,
)
from ai.backend.manager.services.image.actions.forget import (
    ForgetImageAction,
    ForgetImageActionResult,
    ForgetImageActionSuccess,
)
from ai.backend.manager.services.image.processors import ImageProcessors

from .conftest import TestScenario

IMAGE_ROW_FIXTURE = ImageRow(
    name="stable/python",
    image="cr.backend.ai/stable/python:3.9-ubuntu20.04",
    project="stable",
    registry="cr.backend.ai",
    registry_id="11111111-1111-1111-1111-111111111111",
    architecture="x86_64",
    config_digest="sha256:abcdefgh0123456789abcdefgh0123456789abcdefgh0123456789abcd",
    size_bytes=12345678,
    is_local=False,
    type="COMPUTE",
    labels={},
    resources={"cpu": {"min": "500m", "max": None}},
    status="ALIVE",
)
IMAGE_ROW_FIXTURE.id = uuid.uuid4()


@pytest.mark.asyncio
@pytest.mark.parametrize(
    "test_scenario",
    [
        TestScenario.success(
            "Success Case",
            ForgetImageAction(
                user_id=uuid.uuid4(),
                client_role=UserRole.SUPERADMIN,
                reference=IMAGE_ROW_FIXTURE.name,
                architecture=IMAGE_ROW_FIXTURE.architecture,
            ),
            ForgetImageActionSuccess(image_row=IMAGE_ROW_FIXTURE),
        ),
        # TestScenario.failure(
        #     "When No Image exists, raise Image Not Found Error", ForgetImageAction(), BackendError
        # ),
    ],
)
@pytest.mark.parametrize(
    "extra_fixtures",
    [
        {
            "images": [
                {
                    "id": str(IMAGE_ROW_FIXTURE.id),
                    "name": IMAGE_ROW_FIXTURE.name,
                    "image": IMAGE_ROW_FIXTURE.image,
                    "project": IMAGE_ROW_FIXTURE.project,
                    "registry": IMAGE_ROW_FIXTURE.registry,
                    "registry_id": IMAGE_ROW_FIXTURE.registry_id,
                    "architecture": IMAGE_ROW_FIXTURE.architecture,
                    "config_digest": IMAGE_ROW_FIXTURE.config_digest,
                    "size_bytes": IMAGE_ROW_FIXTURE.size_bytes,
                    "is_local": IMAGE_ROW_FIXTURE.is_local,
                    "type": str(IMAGE_ROW_FIXTURE.type),
                    "labels": IMAGE_ROW_FIXTURE.labels,
                    "resources": IMAGE_ROW_FIXTURE.resources,
                    "status": str(IMAGE_ROW_FIXTURE.status),
                }
            ]
        }
    ],
    ids=[""],
)
async def test_forget_images(
    test_scenario: TestScenario[ForgetImageAction, ForgetImageActionResult],
    etcd_fixture,
    extra_fixtures,
    database_fixture,
    create_app_and_client,
):
    app, _ = await create_app_and_client(
        [
            shared_config_ctx,
            database_ctx,
            monitoring_ctx,
            hook_plugin_ctx,
            redis_ctx,
            event_dispatcher_ctx,
            storage_manager_ctx,
            network_plugin_ctx,
            agent_registry_ctx,
            services_ctx,
            processors_ctx,
            background_task_ctx,
        ],
        [".events", ".auth"],
    )
    root_ctx: RootContext = app["_root.context"]
    processors: ImageProcessors = root_ctx.processors.image

    await test_scenario.test(processors.forget_image.wait_for_complete)


# @pytest.mark.parametrize(
#     "test_scenario",
#     [
#         TestScenario.success("Success Case", PurgeImagesAction(), PurgeImagesActionResult()),
#         TestScenario.failure(
#             "When No Image exists, raise Image Not Found Error",
#             PurgeImagesAction(),
#             BackendError,
#         ),
#     ],
# )
# def test_purge_images(
#     test_scenario: TestScenario[PurgeImagesAction, PurgeImagesActionResult],
#     processors: ImageProcessors,
# ):
#     # test_scenario.test(processors.purge_images.fire_and_forget)
#     pass
