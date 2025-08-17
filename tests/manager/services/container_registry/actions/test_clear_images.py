import pytest

from ai.backend.manager.data.image.types import ImageStatus
from ai.backend.manager.models.image import ImageIdentifier, ImageRow
from ai.backend.manager.models.utils import ExtendedAsyncSAEngine
from ai.backend.manager.services.container_registry.actions.clear_images import (
    ClearImagesAction,
    ClearImagesActionResult,
)
from ai.backend.manager.services.container_registry.processors import ContainerRegistryProcessors

from ...fixtures import (
    CONTAINER_REGISTRY_FIXTURE_DATA,
    CONTAINER_REGISTRY_FIXTURE_DICT,
    CONTAINER_REGISTRY_ROW_FIXTURE,
    IMAGE_FIXTURE_DICT,
    IMAGE_ROW_FIXTURE,
)
from ...utils import ScenarioBase


@pytest.mark.parametrize(
    "test_scenario",
    [
        ScenarioBase.success(
            "Success Case",
            ClearImagesAction(
                registry=CONTAINER_REGISTRY_ROW_FIXTURE.registry_name,
                project=CONTAINER_REGISTRY_ROW_FIXTURE.project,
            ),
            ClearImagesActionResult(registry=CONTAINER_REGISTRY_FIXTURE_DATA),
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
                CONTAINER_REGISTRY_FIXTURE_DICT,
            ],
        }
    ],
)
async def test_clear_images(
    processors: ContainerRegistryProcessors,
    test_scenario: ScenarioBase[ClearImagesAction, ClearImagesActionResult],
):
    await test_scenario.test(processors.clear_images.wait_for_complete)


@pytest.mark.parametrize(
    "extra_fixtures",
    [
        {
            "images": [
                IMAGE_FIXTURE_DICT,
            ],
            "container_registries": [
                CONTAINER_REGISTRY_FIXTURE_DICT,
            ],
        }
    ],
)
async def test_clear_images_side_effect(
    processors: ContainerRegistryProcessors,
    database_engine: ExtendedAsyncSAEngine,
):
    await processors.clear_images.wait_for_complete(
        ClearImagesAction(
            registry=CONTAINER_REGISTRY_ROW_FIXTURE.registry_name,
            project=CONTAINER_REGISTRY_ROW_FIXTURE.project,
        ),
    )

    async with database_engine.begin_session() as db_sess:
        result = await ImageRow.resolve(
            db_sess,
            [
                ImageIdentifier(
                    canonical=IMAGE_ROW_FIXTURE.name,
                    architecture=IMAGE_ROW_FIXTURE.architecture,
                )
            ],
            filter_by_statuses=[ImageStatus.DELETED],
        )

        assert result.status is ImageStatus.DELETED, (
            "Image should be marked with deleted in the database"
        )
