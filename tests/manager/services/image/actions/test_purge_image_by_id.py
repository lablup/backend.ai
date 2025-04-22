import uuid

import pytest

from ai.backend.manager.models.user import UserRole
from ai.backend.manager.services.image.actions.purge_image_by_id import (
    PurgeImageActionByIdGenericForbiddenError,
    PurgeImageActionByIdObjectNotFoundError,
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
