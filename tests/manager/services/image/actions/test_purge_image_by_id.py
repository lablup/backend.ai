import uuid

import pytest
import sqlalchemy as sa

from ai.backend.manager.errors.image import ForgetImageForbiddenError, ImageNotFound
from ai.backend.manager.models.image import ImageRow
from ai.backend.manager.models.user import UserRole
from ai.backend.manager.models.utils import ExtendedAsyncSAEngine
from ai.backend.manager.services.image.actions.purge_image_by_id import (
    PurgeImageByIdAction,
    PurgeImageByIdActionResult,
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
            ForgetImageForbiddenError,
        ),
        TestScenario.failure(
            "Image not found",
            PurgeImageByIdAction(
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
async def test_purge_image_by_id(
    processors: ImageProcessors,
    test_scenario: TestScenario[PurgeImageByIdAction, PurgeImageByIdActionResult],
):
    await test_scenario.test(processors.purge_image_by_id.wait_for_complete)


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
async def test_purge_image_by_id_side_effect(
    processors: ImageProcessors,
    database_engine: ExtendedAsyncSAEngine,
):
    await processors.purge_image_by_id.wait_for_complete(
        PurgeImageByIdAction(
            user_id=uuid.uuid4(),
            client_role=UserRole.SUPERADMIN,
            image_id=IMAGE_ROW_FIXTURE.id,
        )
    )

    async with database_engine.begin_session() as db_sess:
        db_row = await db_sess.scalar(
            sa.select(ImageRow).where(ImageRow.id == IMAGE_ROW_FIXTURE.id)
        )
        assert db_row is None, "Image should be deleted from the database"
