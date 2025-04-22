import pytest

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
)
from ...test_utils import TestScenario


@pytest.mark.parametrize(
    "test_scenario",
    [
        TestScenario.success(
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
    test_scenario: TestScenario[ClearImagesAction, ClearImagesActionResult],
):
    await test_scenario.test(processors.clear_images.wait_for_complete)
