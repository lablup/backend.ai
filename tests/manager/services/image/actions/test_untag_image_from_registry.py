import uuid
from unittest.mock import AsyncMock

import pytest

from ai.backend.manager.errors.image import (
    ForgetImageForbiddenError,
    ImageNotFound,
)
from ai.backend.manager.models.user import UserRole
from ai.backend.manager.services.image.actions.untag_image_from_registry import (
    UntagImageFromRegistryAction,
    UntagImageFromRegistryActionResult,
)
from ai.backend.manager.services.image.processors import ImageProcessors

from ...fixtures import (
    CONTAINER_REGISTRY_FIXTURE_DICT,
    IMAGE_FIXTURE_DATA,
    IMAGE_FIXTURE_DICT,
    IMAGE_ROW_FIXTURE,
)
from ...utils import ScenarioBase


@pytest.fixture
def mock_harbor_v2_untag(mocker):
    mock = mocker.patch(
        "ai.backend.manager.container_registry.harbor.HarborRegistry_v2.untag",
        new_callable=AsyncMock,
    )
    mock.return_value = None
    return mock


HARBOR2_REGISTRY_FIXTURE_DICT = {**CONTAINER_REGISTRY_FIXTURE_DICT}
HARBOR2_REGISTRY_FIXTURE_DICT["type"] = "harbor2"


@pytest.mark.parametrize(
    "test_scenario",
    [
        ScenarioBase.success(
            "Success Case",
            UntagImageFromRegistryAction(
                user_id=uuid.uuid4(),
                client_role=UserRole.SUPERADMIN,
                image_id=IMAGE_ROW_FIXTURE.id,
            ),
            UntagImageFromRegistryActionResult(
                image=IMAGE_FIXTURE_DATA,
            ),
        ),
        ScenarioBase.failure(
            "When the user is not SUPERADMIN, and the user is not the image's owner, raise Generic Forbidden Error",
            UntagImageFromRegistryAction(
                user_id=uuid.uuid4(),
                client_role=UserRole.USER,
                image_id=IMAGE_ROW_FIXTURE.id,
            ),
            ForgetImageForbiddenError,
        ),
        ScenarioBase.failure(
            "Image not found",
            UntagImageFromRegistryAction(
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
            ],
            "container_registries": [
                HARBOR2_REGISTRY_FIXTURE_DICT,
            ],
        }
    ],
)
async def test_untag_image_from_registry(
    mock_harbor_v2_untag,
    processors: ImageProcessors,
    test_scenario: ScenarioBase[UntagImageFromRegistryAction, UntagImageFromRegistryActionResult],
):
    await test_scenario.test(processors.untag_image_from_registry.wait_for_complete)
