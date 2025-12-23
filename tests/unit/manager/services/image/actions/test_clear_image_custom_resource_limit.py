import copy

import pytest

from ai.backend.common.types import SlotName
from ai.backend.manager.models.image import ImageIdentifier, ImageRow
from ai.backend.manager.models.utils import ExtendedAsyncSAEngine
from ai.backend.manager.services.image.actions.clear_image_custom_resource_limit import (
    ClearImageCustomResourceLimitAction,
    ClearImageCustomResourceLimitActionResult,
)
from ai.backend.manager.services.image.processors import ImageProcessors

from ...fixtures import (
    IMAGE_FIXTURE_DATA,
    IMAGE_FIXTURE_DICT,
)
from ...utils import ScenarioBase

EXPECTED_IMAGE_DATA = copy.deepcopy(IMAGE_FIXTURE_DATA)
# Intrinsic cpu, and mem resource limits exist.
EXPECTED_IMAGE_DATA.resources.resources_data.pop(SlotName("cuda.device"))


@pytest.mark.parametrize(
    "test_scenario",
    [
        ScenarioBase.success(
            "Success Case",
            ClearImageCustomResourceLimitAction(
                image_canonical=IMAGE_FIXTURE_DATA.name,
                architecture=IMAGE_FIXTURE_DATA.architecture,
            ),
            ClearImageCustomResourceLimitActionResult(
                image_data=EXPECTED_IMAGE_DATA,
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
        }
    ],
)
async def test_clear_image_custom_resource_limit(
    processors: ImageProcessors,
    test_scenario: ScenarioBase[
        ClearImageCustomResourceLimitAction, ClearImageCustomResourceLimitActionResult
    ],
):
    await test_scenario.test(processors.clear_image_custom_resource_limit.wait_for_complete)


@pytest.mark.parametrize(
    "extra_fixtures",
    [
        {
            "images": [
                IMAGE_FIXTURE_DICT,
            ],
        }
    ],
)
async def test_clear_image_custom_resource_limit_side_effect(
    processors: ImageProcessors,
    database_engine: ExtendedAsyncSAEngine,
):
    await processors.clear_image_custom_resource_limit.wait_for_complete(
        ClearImageCustomResourceLimitAction(
            image_canonical=IMAGE_FIXTURE_DATA.name,
            architecture=IMAGE_FIXTURE_DATA.architecture,
        ),
    )

    async with database_engine.begin_session() as db_sess:
        db_row = await ImageRow.resolve(
            db_sess,
            [
                ImageIdentifier(
                    canonical=IMAGE_FIXTURE_DATA.name,
                    architecture=IMAGE_FIXTURE_DATA.architecture,
                )
            ],
        )
        assert db_row.resources.get(SlotName("cuda.device")) is None, (
            "Resource limit should be cleared"
        )
