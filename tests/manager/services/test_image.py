import uuid

import pytest

from ai.backend.manager.api.exceptions import ImageNotFound
from ai.backend.manager.models.image import ImageAliasRow, ImageRow, ImageStatus, ImageType
from ai.backend.manager.models.user import UserRole
from ai.backend.manager.server import (
    agent_registry_ctx,
)
from ai.backend.manager.services.image.actions.dealias_image import (
    DealiasImageAction,
    DealiasImageActionResult,
)
from ai.backend.manager.services.image.actions.forget_image import (
    ForgetImageAction,
    ForgetImageActionGenericForbiddenError,
    ForgetImageActionResult,
)
from ai.backend.manager.services.image.actions.forget_image_by_id import (
    ForgetImageActionByIdGenericForbiddenError,
    ForgetImageActionByIdObjectNotFoundError,
    ForgetImageByIdAction,
    ForgetImageByIdActionResult,
)
from ai.backend.manager.services.image.processors import ImageProcessors
from ai.backend.manager.services.image.service import ImageService

from .conftest import TestScenario

IMAGE_ROW_FIXTURE = ImageRow(
    name="cr.backend.ai/stable/python:3.9-ubuntu20.04",
    image="stable/python",
    project="stable",
    registry="cr.backend.ai",
    registry_id="11111111-1111-1111-1111-111111111111",
    architecture="x86_64",
    config_digest="sha256:abcdefgh0123456789abcdefgh0123456789abcdefgh0123456789abcd",
    size_bytes=12345678,
    is_local=False,
    type=ImageType.COMPUTE,
    labels={},
    resources={"cpu": {"min": "500m", "max": None}},
    status=ImageStatus.ALIVE,
)
IMAGE_ROW_FIXTURE.id = uuid.uuid4()

IMAGE_ALIAS_ROW_FIXTURE = ImageAliasRow(
    id=uuid.uuid4(),
    alias="python",
    image_id=IMAGE_ROW_FIXTURE.id,
)


@pytest.fixture
def processors(extra_fixtures, database_fixture, database_engine):
    image_service = ImageService(db=database_engine, agent_registry=agent_registry_ctx)
    return ImageProcessors(image_service)


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
            ForgetImageActionResult(image=IMAGE_ROW_FIXTURE),
        ),
        TestScenario.failure(
            "When the user is not SUPERADMIN, and the user is not the image's owner, raise Generic Forbidden Error",
            ForgetImageAction(
                user_id=uuid.uuid4(),
                client_role=UserRole.USER,
                reference=IMAGE_ROW_FIXTURE.name,
                architecture=IMAGE_ROW_FIXTURE.architecture,
            ),
            ForgetImageActionGenericForbiddenError,
        ),
        TestScenario.failure(
            "Image not found",
            ForgetImageAction(
                user_id=uuid.uuid4(),
                client_role=UserRole.SUPERADMIN,
                reference="wrong-image",
                architecture=IMAGE_ROW_FIXTURE.architecture,
            ),
            # TODO: 여기서 ImageNotFound를 사용하는게 맞는지?
            # 아니면 새로운 Exception을 만들어야 하는지?
            ImageNotFound,
        ),
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
                    "type": IMAGE_ROW_FIXTURE.type._name_,
                    "labels": IMAGE_ROW_FIXTURE.labels,
                    "resources": IMAGE_ROW_FIXTURE.resources,
                    "status": IMAGE_ROW_FIXTURE.status.value,
                }
            ]
        }
    ],
    ids=[""],
)
async def test_forget_image(
    processors: ImageProcessors,
    test_scenario: TestScenario[ForgetImageAction, ForgetImageActionResult],
):
    # TODO: forget_image가 성공했을 때 DB에 내용 반영된 것은 여기에 별도로 로직 넣어 확인해야 하는지?
    await test_scenario.test(processors.forget_image.wait_for_complete)


@pytest.mark.asyncio
@pytest.mark.parametrize(
    "test_scenario",
    [
        TestScenario.success(
            "Success Case",
            ForgetImageByIdAction(
                user_id=uuid.uuid4(),
                client_role=UserRole.SUPERADMIN,
                image_id=IMAGE_ROW_FIXTURE.id,
            ),
            ForgetImageByIdActionResult(image=IMAGE_ROW_FIXTURE),
        ),
        TestScenario.failure(
            "When the user is not SUPERADMIN, and the user is not the image's owner, raise Generic Forbidden Error",
            ForgetImageByIdAction(
                user_id=uuid.uuid4(),
                client_role=UserRole.USER,
                image_id=IMAGE_ROW_FIXTURE.id,
            ),
            ForgetImageActionByIdGenericForbiddenError,
        ),
        TestScenario.failure(
            "Image not found",
            ForgetImageByIdAction(
                user_id=uuid.uuid4(),
                client_role=UserRole.SUPERADMIN,
                image_id=uuid.UUID("00000000-0000-0000-0000-000000000000"),  # wrong image_id
            ),
            ForgetImageActionByIdObjectNotFoundError,
        ),
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
                    "type": IMAGE_ROW_FIXTURE.type._name_,
                    "labels": IMAGE_ROW_FIXTURE.labels,
                    "resources": IMAGE_ROW_FIXTURE.resources,
                    "status": IMAGE_ROW_FIXTURE.status.value,
                }
            ]
        }
    ],
    ids=[""],
)
async def test_forget_image_by_id(
    processors: ImageProcessors,
    test_scenario: TestScenario[ForgetImageByIdAction, ForgetImageByIdActionResult],
):
    await test_scenario.test(processors.forget_image_by_id.wait_for_complete)


# TODO: 아래 테스트는 작동하지만, image 삭제할 때 image alias fk 위반 에러 발생함.
# @pytest.mark.asyncio
# @pytest.mark.parametrize(
#     "test_scenario",
#     [
#         TestScenario.success(
#             "Success Case",
#             AliasImageAction(
#                 image_canonical=IMAGE_ROW_FIXTURE.name,
#                 architecture=IMAGE_ROW_FIXTURE.architecture,
#                 alias="new-alias",
#             ),
#             AliasImageActionResult(image_alias=ImageAliasRow(
#                 id=uuid.uuid4(),
#                 alias="new-alias",
#                 image_id=IMAGE_ROW_FIXTURE.id,
#             )),
#         ),
#     ],
# )
# @pytest.mark.parametrize(
#     "extra_fixtures",
#     [
#         {
#             "images": [
#                 {
#                     "id": str(IMAGE_ROW_FIXTURE.id),
#                     "name": IMAGE_ROW_FIXTURE.name,
#                     "image": IMAGE_ROW_FIXTURE.image,
#                     "project": IMAGE_ROW_FIXTURE.project,
#                     "registry": IMAGE_ROW_FIXTURE.registry,
#                     "registry_id": IMAGE_ROW_FIXTURE.registry_id,
#                     "architecture": IMAGE_ROW_FIXTURE.architecture,
#                     "config_digest": IMAGE_ROW_FIXTURE.config_digest,
#                     "size_bytes": IMAGE_ROW_FIXTURE.size_bytes,
#                     "is_local": IMAGE_ROW_FIXTURE.is_local,
#                     "type": IMAGE_ROW_FIXTURE.type._name_,
#                     "labels": IMAGE_ROW_FIXTURE.labels,
#                     "resources": IMAGE_ROW_FIXTURE.resources,
#                     "status": IMAGE_ROW_FIXTURE.status.value,
#                 }
#             ],
#         }
#     ],
#     ids=[""],
# )
# async def test_alias_image(
#     processors: ImageProcessors,
#     test_scenario: TestScenario[AliasImageAction, AliasImageActionResult],
# ):
#     await test_scenario.test(processors.alias_image.wait_for_complete)


@pytest.mark.asyncio
@pytest.mark.parametrize(
    "test_scenario",
    [
        TestScenario.success(
            "Success Case",
            DealiasImageAction(
                alias=IMAGE_ALIAS_ROW_FIXTURE.alias,
            ),
            DealiasImageActionResult(
                image_id=IMAGE_ALIAS_ROW_FIXTURE.image_id, image_alias=IMAGE_ALIAS_ROW_FIXTURE
            ),
        ),
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
                    "type": IMAGE_ROW_FIXTURE.type._name_,
                    "labels": IMAGE_ROW_FIXTURE.labels,
                    "resources": IMAGE_ROW_FIXTURE.resources,
                    "status": IMAGE_ROW_FIXTURE.status.value,
                }
            ],
            "image_aliases": [
                {
                    "id": str(IMAGE_ALIAS_ROW_FIXTURE.id),
                    "alias": IMAGE_ALIAS_ROW_FIXTURE.alias,
                    "image": str(IMAGE_ROW_FIXTURE.id),
                }
            ],
        }
    ],
    ids=[""],
)
async def test_dealias_image(
    processors: ImageProcessors,
    test_scenario: TestScenario[DealiasImageAction, DealiasImageActionResult],
):
    await test_scenario.test(processors.dealias_image.wait_for_complete)


# TODO: 일단 ClearImages에서 뭔가를 리턴해야...?
# @pytest.mark.asyncio
# @pytest.mark.parametrize(
#     "test_scenario",
#     [
#         TestScenario.success(
#             "Success Case",
#             ClearImagesAction(
#                 registry=IMAGE_ROW_FIXTURE.registry,
#             ),
#             ClearImagesActionResult(),
#         ),
#     ],
# )
# @pytest.mark.parametrize(
#     "extra_fixtures",
#     [
#         {
#             "images": [
#                 {
#                     "id": str(IMAGE_ROW_FIXTURE.id),
#                     "name": IMAGE_ROW_FIXTURE.name,
#                     "image": IMAGE_ROW_FIXTURE.image,
#                     "project": IMAGE_ROW_FIXTURE.project,
#                     "registry": IMAGE_ROW_FIXTURE.registry,
#                     "registry_id": IMAGE_ROW_FIXTURE.registry_id,
#                     "architecture": IMAGE_ROW_FIXTURE.architecture,
#                     "config_digest": IMAGE_ROW_FIXTURE.config_digest,
#                     "size_bytes": IMAGE_ROW_FIXTURE.size_bytes,
#                     "is_local": IMAGE_ROW_FIXTURE.is_local,
#                     "type": IMAGE_ROW_FIXTURE.type._name_,
#                     "labels": IMAGE_ROW_FIXTURE.labels,
#                     "resources": IMAGE_ROW_FIXTURE.resources,
#                     "status": IMAGE_ROW_FIXTURE.status.value,
#                 }
#             ],
#             "image_aliases": [
#                 {
#                     "id": str(IMAGE_ALIAS_ROW_FIXTURE.id),
#                     "alias": IMAGE_ALIAS_ROW_FIXTURE.alias,
#                     "image": str(IMAGE_ROW_FIXTURE.id),
#                 }
#             ],
#         }
#     ],
#     ids=[""],
# )
# async def test_clear_images(
#     processors: ImageProcessors,
#     test_scenario: TestScenario[ClearImagesAction, ClearImagesActionResult],
# ):
#     await test_scenario.test(processors.clear_images.wait_for_complete)


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
