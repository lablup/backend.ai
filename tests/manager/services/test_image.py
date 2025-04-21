import dataclasses
import uuid
from dataclasses import replace

import pytest
from dateutil.parser import isoparse

from ai.backend.common.types import SlotName
from ai.backend.manager.api.exceptions import ImageNotFound
from ai.backend.manager.data.image.types import ImageLabelsData, ImageResourcesData
from ai.backend.manager.models.image import ImageAliasRow, ImageRow, ImageStatus, ImageType
from ai.backend.manager.models.user import UserRole
from ai.backend.manager.server import (
    agent_registry_ctx,
)
from ai.backend.manager.services.image.actions.alias_image import (
    AliasImageAction,
    AliasImageActionResult,
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
from ai.backend.manager.services.image.actions.modify_image import (
    ImageModifier,
    ModifyImageAction,
    ModifyImageActionResult,
    ModifyImageActionValueError,
)
from ai.backend.manager.services.image.actions.purge_image_by_id import (
    PurgeImageActionByIdGenericForbiddenError,
    PurgeImageActionByIdObjectNotFoundError,
    PurgeImageByIdAction,
    PurgeImageByIdActionResult,
)
from ai.backend.manager.services.image.processors import ImageProcessors
from ai.backend.manager.services.image.service import ImageService
from ai.backend.manager.types import OptionalState, TriState

from .test_utils import TestScenario

IMAGE_ROW_FIXTURE = ImageRow(
    name="cr.backend.ai/stable/python:3.9-ubuntu20.04",
    image="stable/python",
    project="stable",
    registry="cr.backend.ai",
    registry_id=uuid.UUID("11111111-1111-1111-1111-111111111111"),
    architecture="x86_64",
    accelerators="cuda",
    config_digest="sha256:abcdefgh0123456789abcdefgh0123456789abcdefgh0123456789abcd".ljust(
        72, " "
    ),  # config_digest column is sa.CHAR(length=72)
    size_bytes=12345678,
    is_local=False,
    type=ImageType.COMPUTE,
    labels={},
    resources={},
    status=ImageStatus.ALIVE,
)
IMAGE_ROW_FIXTURE.created_at = isoparse("2023-10-01T00:00:00+09:00")
IMAGE_ROW_FIXTURE.id = uuid.uuid4()

IMAGE_ALIAS_ROW_FIXTURE = ImageAliasRow(
    id=uuid.uuid4(),
    alias="python",
    image_id=IMAGE_ROW_FIXTURE.id,
)

IMAGE_FIXTURE_DATA = IMAGE_ROW_FIXTURE.to_dataclass()
IMAGE_ALIAS_DATA = IMAGE_ALIAS_ROW_FIXTURE.to_dataclass()


IMAGE_FIXTURE_DICT = dataclasses.asdict(
    dataclasses.replace(IMAGE_FIXTURE_DATA, type=ImageType.COMPUTE._name_, labels={}, resources={})  # type: ignore
)

IMAGE_ALIAS_DICT = dataclasses.asdict(IMAGE_ALIAS_DATA)
IMAGE_ALIAS_DICT["image"] = IMAGE_ALIAS_ROW_FIXTURE.image_id


@pytest.fixture
def processors(extra_fixtures, database_fixture, database_engine):
    image_service = ImageService(db=database_engine, agent_registry=agent_registry_ctx)
    return ImageProcessors(image_service, [])


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
            ForgetImageActionResult(image=replace(IMAGE_FIXTURE_DATA, status=ImageStatus.DELETED)),
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
            ImageNotFound,
        ),
    ],
)
@pytest.mark.parametrize(
    "extra_fixtures",
    [
        {
            "images": [
                IMAGE_FIXTURE_DICT,
            ]
        }
    ],
)
async def test_forget_image(
    processors: ImageProcessors,
    test_scenario: TestScenario[ForgetImageAction, ForgetImageActionResult],
):
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
            ForgetImageByIdActionResult(
                image=replace(IMAGE_FIXTURE_DATA, status=ImageStatus.DELETED)
            ),
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
                IMAGE_FIXTURE_DICT,
            ]
        }
    ],
)
async def test_forget_image_by_id(
    processors: ImageProcessors,
    test_scenario: TestScenario[ForgetImageByIdAction, ForgetImageByIdActionResult],
):
    await test_scenario.test(processors.forget_image_by_id.wait_for_complete)


@pytest.mark.asyncio
@pytest.mark.parametrize(
    "test_scenario",
    [
        TestScenario.success(
            "Success Case",
            PurgeImageByIdAction(
                user_id=uuid.uuid4(),
                client_role=UserRole.SUPERADMIN,
                image_id=IMAGE_ROW_FIXTURE.id,
            ),
            PurgeImageByIdActionResult(image=IMAGE_FIXTURE_DATA),
        ),
        TestScenario.failure(
            "When the user is not SUPERADMIN, and the user is not the image's owner, raise Generic Forbidden Error",
            PurgeImageByIdAction(
                user_id=uuid.uuid4(),
                client_role=UserRole.USER,
                image_id=IMAGE_ROW_FIXTURE.id,
            ),
            PurgeImageActionByIdGenericForbiddenError,
        ),
        TestScenario.failure(
            "Image not found",
            PurgeImageByIdAction(
                user_id=uuid.uuid4(),
                client_role=UserRole.SUPERADMIN,
                image_id=uuid.UUID("00000000-0000-0000-0000-000000000000"),  # wrong image_id
            ),
            PurgeImageActionByIdObjectNotFoundError,
        ),
    ],
)
@pytest.mark.parametrize(
    "extra_fixtures",
    [
        {
            "images": [
                IMAGE_FIXTURE_DICT,
            ]
        }
    ],
)
async def test_purge_image_by_id(
    processors: ImageProcessors,
    test_scenario: TestScenario[PurgeImageByIdAction, PurgeImageByIdActionResult],
):
    await test_scenario.test(processors.purge_image_by_id.wait_for_complete)


@pytest.mark.asyncio
@pytest.mark.parametrize(
    "test_scenario",
    [
        TestScenario.success(
            "Success Case",
            AliasImageAction(
                image_canonical=IMAGE_ROW_FIXTURE.name,
                architecture=IMAGE_ROW_FIXTURE.architecture,
                alias="python",
            ),
            AliasImageActionResult(
                image_id=IMAGE_ROW_FIXTURE.id,
                image_alias=IMAGE_ALIAS_DATA,
            ),
        ),
    ],
)
@pytest.mark.parametrize(
    "extra_fixtures",
    [
        {
            "images": [IMAGE_FIXTURE_DICT],
        }
    ],
)
async def test_alias_image(
    processors: ImageProcessors,
    test_scenario: TestScenario[AliasImageAction, AliasImageActionResult],
):
    await test_scenario.test(processors.alias_image.wait_for_complete)


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
                image_id=IMAGE_ALIAS_ROW_FIXTURE.image_id, image_alias=IMAGE_ALIAS_DATA
            ),
        ),
    ],
)
@pytest.mark.parametrize(
    "extra_fixtures",
    [
        {
            "images": [
                IMAGE_FIXTURE_DICT,
            ],
            "image_aliases": [
                IMAGE_ALIAS_DICT,
            ],
        }
    ],
)
async def test_dealias_image(
    processors: ImageProcessors,
    test_scenario: TestScenario[DealiasImageAction, DealiasImageActionResult],
):
    await test_scenario.test(processors.dealias_image.wait_for_complete)


@pytest.mark.asyncio
@pytest.mark.parametrize(
    "test_scenario",
    [
        TestScenario.success(
            "Update one column",
            ModifyImageAction(
                target=IMAGE_ROW_FIXTURE.name,
                architecture=IMAGE_ROW_FIXTURE.architecture,
                modifier=ImageModifier(
                    registry=OptionalState.update("cr.backend.ai2"),
                ),
            ),
            ModifyImageActionResult(image=replace(IMAGE_FIXTURE_DATA, registry="cr.backend.ai2")),
        ),
        TestScenario.success(
            "Make a column empty",
            ModifyImageAction(
                target=IMAGE_ROW_FIXTURE.name,
                architecture=IMAGE_ROW_FIXTURE.architecture,
                modifier=ImageModifier(
                    accelerators=TriState.nullify(),
                ),
            ),
            ModifyImageActionResult(image=replace(IMAGE_FIXTURE_DATA, accelerators=None)),
        ),
        TestScenario.success(
            "Update multiple columns",
            ModifyImageAction(
                target=IMAGE_ROW_FIXTURE.name,
                architecture=IMAGE_ROW_FIXTURE.architecture,
                modifier=ImageModifier(
                    type=OptionalState.update(ImageType.SERVICE),
                    registry=OptionalState.update("cr.backend.ai2"),
                    accelerators=TriState.update(value="cuda,rocm"),
                    is_local=OptionalState.update(True),
                    size_bytes=OptionalState.update(123),
                    labels=OptionalState.update({"key1": "value1", "key2": "value2"}),
                    resources=OptionalState.update(
                        {
                            "cpu": {"min": "3", "max": "5"},
                            "mem": {"min": "256m", "max": None},
                            "cuda.device": {"max": None, "min": "1"},
                        },
                    ),
                    config_digest=OptionalState.update("sha256:1234567890abcdef"),
                ),
            ),
            ModifyImageActionResult(
                image=replace(
                    IMAGE_FIXTURE_DATA,
                    type=ImageType.SERVICE,
                    registry="cr.backend.ai2",
                    accelerators="cuda,rocm",
                    is_local=True,
                    size_bytes=123,
                    labels=ImageLabelsData(label_data={"key1": "value1", "key2": "value2"}),
                    resources=ImageResourcesData(
                        resources_data={
                            SlotName("cpu"): {"min": "3", "max": "5"},
                            SlotName("mem"): {"min": "256m", "max": None},
                            SlotName("cuda.device"): {"max": None, "min": "1"},
                        }
                    ),
                    config_digest="sha256:1234567890abcdef",
                )
            ),
        ),
        TestScenario.success(
            "Update one column by image alias",
            ModifyImageAction(
                target=IMAGE_ALIAS_ROW_FIXTURE.alias,
                architecture=IMAGE_ROW_FIXTURE.architecture,
                modifier=ImageModifier(
                    registry=OptionalState.update("cr.backend.ai2"),
                ),
            ),
            ModifyImageActionResult(image=replace(IMAGE_FIXTURE_DATA, registry="cr.backend.ai2")),
        ),
        TestScenario.failure(
            "Image not found",
            ModifyImageAction(
                target="wrong-image",
                architecture=IMAGE_ROW_FIXTURE.architecture,
                modifier=ImageModifier(
                    registry=OptionalState.update("cr.backend.ai2"),
                ),
            ),
            ImageNotFound,
        ),
        TestScenario.failure(
            "Value Error",
            ModifyImageAction(
                target=IMAGE_ROW_FIXTURE.name,
                architecture=IMAGE_ROW_FIXTURE.architecture,
                modifier=ImageModifier(
                    config_digest=OptionalState.update(
                        "a" * 73
                    ),  # config_digest column is sa.CHAR(length=72)
                ),
            ),
            ModifyImageActionValueError,
        ),
    ],
)
@pytest.mark.parametrize(
    "extra_fixtures",
    [
        {
            "images": [
                IMAGE_FIXTURE_DICT,
            ],
            "image_aliases": [
                IMAGE_ALIAS_DICT,
            ],
        }
    ],
)
async def test_modify_image(
    processors: ImageProcessors,
    test_scenario: TestScenario[ModifyImageAction, ModifyImageActionResult],
):
    await test_scenario.test(processors.modify_image.wait_for_complete)
