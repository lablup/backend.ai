import pytest
import sqlalchemy as sa

from ai.backend.manager.models.image import ImageAliasRow
from ai.backend.manager.models.utils import ExtendedAsyncSAEngine
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
from ...utils import ScenarioBase


@pytest.mark.parametrize(
    "test_scenario",
    [
        ScenarioBase.success(
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
    test_scenario: ScenarioBase[AliasImageAction, AliasImageActionResult],
):
    await test_scenario.test(processors.alias_image.wait_for_complete)


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
async def test_alias_image_side_effect(
    processors: ImageProcessors,
    database_engine: ExtendedAsyncSAEngine,
):
    await processors.alias_image.wait_for_complete(
        AliasImageAction(
            image_canonical=IMAGE_ROW_FIXTURE.name,
            architecture=IMAGE_ROW_FIXTURE.architecture,
            alias="python",
        )
    )

    async with database_engine.begin_session() as db_sess:
        db_row = await db_sess.scalar(
            sa.select(ImageAliasRow).where(ImageAliasRow.alias == "python")
        )
        assert db_row is not None, "Image alias should be created in the database"
