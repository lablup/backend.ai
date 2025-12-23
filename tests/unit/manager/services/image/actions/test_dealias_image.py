import pytest
import sqlalchemy as sa

from ai.backend.manager.models.image import ImageAliasRow
from ai.backend.manager.models.utils import ExtendedAsyncSAEngine
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
from ...utils import ScenarioBase


@pytest.mark.parametrize(
    "test_scenario",
    [
        ScenarioBase.success(
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
    test_scenario: ScenarioBase[DealiasImageAction, DealiasImageActionResult],
):
    await test_scenario.test(processors.dealias_image.wait_for_complete)


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
async def test_dealias_image_side_effect(
    processors: ImageProcessors,
    database_engine: ExtendedAsyncSAEngine,
):
    await processors.dealias_image.wait_for_complete(
        DealiasImageAction(
            alias=IMAGE_ALIAS_ROW_FIXTURE.alias,
        )
    )

    async with database_engine.begin_session() as db_sess:
        db_row = await db_sess.scalar(
            sa.select(ImageAliasRow).where(ImageAliasRow.alias == "python")
        )
        assert db_row is None, "Image alias should be deleted from the database"
