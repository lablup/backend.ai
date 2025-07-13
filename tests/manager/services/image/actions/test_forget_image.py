import uuid
from dataclasses import replace

import pytest

from ai.backend.manager.errors.exceptions import (
    ForgetImageActionGenericForbiddenError,
    ImageNotFound,
)
from ai.backend.manager.models.image import ImageIdentifier, ImageRow, ImageStatus
from ai.backend.manager.models.user import UserRole
from ai.backend.manager.models.utils import ExtendedAsyncSAEngine
from ai.backend.manager.services.image.actions.forget_image import (
    ForgetImageAction,
    ForgetImageActionResult,
)
from ai.backend.manager.services.image.processors import ImageProcessors

from ...fixtures import (
    IMAGE_FIXTURE_DATA,
    IMAGE_FIXTURE_DICT,
    IMAGE_ROW_FIXTURE,
)
from ...test_utils import TestScenario


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
async def test_forget_image_side_effect(
    processors: ImageProcessors,
    database_engine: ExtendedAsyncSAEngine,
):
    await processors.forget_image.wait_for_complete(
        ForgetImageAction(
            user_id=uuid.uuid4(),
            client_role=UserRole.SUPERADMIN,
            reference=IMAGE_ROW_FIXTURE.name,
            architecture=IMAGE_ROW_FIXTURE.architecture,
        )
    )

    async with database_engine.begin_session() as db_sess:
        db_row = await ImageRow.resolve(
            db_sess,
            [
                ImageIdentifier(
                    canonical=IMAGE_ROW_FIXTURE.name,
                    architecture=IMAGE_ROW_FIXTURE.architecture,
                )
            ],
            filter_by_statuses=[ImageStatus.DELETED],
        )
        assert db_row.status is ImageStatus.DELETED, (
            "Image should be marked with deleted in the database"
        )
