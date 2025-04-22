import pytest

from ai.backend.manager.services.image.actions.alias_image import (
    AliasImageAction,
    AliasImageActionResult,
)
from ai.backend.manager.services.image.processors import ImageProcessors

from ...fixtures import (
    IMAGE_ALIAS_DATA,
    IMAGE_FIXTURE_DICT,
    IMAGE_ROW_FIXTURE,
)
from ...test_utils import TestScenario


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
