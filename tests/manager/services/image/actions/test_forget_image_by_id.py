import uuid
from dataclasses import replace

import pytest

from ai.backend.manager.errors.image import ForgetImageForbiddenError, ImageNotFound
from ai.backend.manager.models.image import ImageRow, ImageStatus
from ai.backend.manager.models.user import UserRole
from ai.backend.manager.models.utils import ExtendedAsyncSAEngine
from ai.backend.manager.services.image.actions.forget_image_by_id import (
    ForgetImageByIdAction,
    ForgetImageByIdActionResult,
)
from ai.backend.manager.services.image.processors import ImageProcessors

from ...fixtures import (
    IMAGE_FIXTURE_DATA,
    IMAGE_FIXTURE_DICT,
    IMAGE_ROW_FIXTURE,
)
from ...utils import ScenarioBase


@pytest.mark.parametrize(
    "test_scenario",
    [
        ScenarioBase.success(
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
        ScenarioBase.failure(
            "When the user is not SUPERADMIN, and the user is not the image's owner, raise Generic Forbidden Error",
            ForgetImageByIdAction(
                user_id=uuid.uuid4(),
                client_role=UserRole.USER,
                image_id=IMAGE_ROW_FIXTURE.id,
            ),
            ForgetImageForbiddenError,
        ),
        ScenarioBase.failure(
            "Image not found",
            ForgetImageByIdAction(
                user_id=uuid.uuid4(),
                client_role=UserRole.SUPERADMIN,
                image_id=uuid.UUID("00000000-0000-0000-0000-000000000000"),  # wrong image_id
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
async def test_forget_image_by_id(
    processors: ImageProcessors,
    test_scenario: ScenarioBase[ForgetImageByIdAction, ForgetImageByIdActionResult],
):
    await test_scenario.test(processors.forget_image_by_id.wait_for_complete)


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
async def test_forget_image_by_id_side_effect(
    processors: ImageProcessors,
    database_engine: ExtendedAsyncSAEngine,
):
    await processors.forget_image_by_id.wait_for_complete(
        ForgetImageByIdAction(
            user_id=uuid.uuid4(),
            client_role=UserRole.SUPERADMIN,
            image_id=IMAGE_ROW_FIXTURE.id,
        )
    )

    async with database_engine.begin_session() as db_sess:
        db_row = await ImageRow.get(
            db_sess, IMAGE_ROW_FIXTURE.id, filter_by_statuses=[ImageStatus.DELETED]
        )
        assert db_row is not None, "Image should not be purged from the database"
        assert db_row.status is ImageStatus.DELETED, (
            "Image should be marked with deleted in the database"
        )
