import pytest

from ai.backend.manager.services.image.actions.dealias_image import (
    DealiasImageAction,
    DealiasImageActionResult,
)
from ai.backend.manager.services.image.processors import ImageProcessors

from ...fixtures import (
    IMAGE_ALIAS_DATA,
    IMAGE_ALIAS_DICT,
    IMAGE_ALIAS_ROW_FIXTURE,
    IMAGE_FIXTURE_DICT,
)
from ...test_utils import TestScenario


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
