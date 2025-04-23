import pytest

from ai.backend.manager.services.container_registry.actions.load_container_registries import (
    LoadContainerRegistriesAction,
    LoadContainerRegistriesActionResult,
)
from ai.backend.manager.services.container_registry.processors import ContainerRegistryProcessors

from ...fixtures import (
    CONTAINER_REGISTRY_FIXTURE_DATA,
    CONTAINER_REGISTRY_FIXTURE_DICT,
    CONTAINER_REGISTRY_ROW_FIXTURE,
)
from ...test_utils import TestScenario


@pytest.mark.parametrize(
    "test_scenario",
    [
        TestScenario.success(
            "Success Case",
            LoadContainerRegistriesAction(
                registry=CONTAINER_REGISTRY_ROW_FIXTURE.registry_name, project=None
            ),
            LoadContainerRegistriesActionResult(
                registries=[
                    CONTAINER_REGISTRY_FIXTURE_DATA,
                ]
            ),
        ),
    ],
)
@pytest.mark.parametrize(
    "extra_fixtures",
    [
        {
            "container_registries": [
                CONTAINER_REGISTRY_FIXTURE_DICT,
            ],
        }
    ],
)
async def test_load_container_registries(
    processors: ContainerRegistryProcessors,
    test_scenario: TestScenario[LoadContainerRegistriesAction, LoadContainerRegistriesActionResult],
):
    await test_scenario.test(processors.load_container_registries.wait_for_complete)
