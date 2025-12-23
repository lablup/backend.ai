import pytest

from ai.backend.manager.services.container_registry.actions.get_container_registries import (
    GetContainerRegistriesAction,
    GetContainerRegistriesActionResult,
)
from ai.backend.manager.services.container_registry.processors import ContainerRegistryProcessors

from ...fixtures import (
    CONTAINER_REGISTRY_FIXTURE_DICT,
)
from ...utils import ScenarioBase


@pytest.mark.parametrize(
    "test_scenario",
    [
        ScenarioBase.success(
            "Success Case",
            GetContainerRegistriesAction(),
            GetContainerRegistriesActionResult(
                registries={
                    # fixtures from fixtures.py
                    "test_project/registry.example.com": "https://registry.example.com/",
                    # fixtures from example-container-registries-harbor.json
                    "community/cr.backend.ai": "https://cr.backend.ai/",
                    "multiarch/cr.backend.ai": "https://cr.backend.ai/",
                    "stable/cr.backend.ai": "https://cr.backend.ai/",
                }
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
async def test_get_container_registries(
    processors: ContainerRegistryProcessors,
    test_scenario: ScenarioBase[GetContainerRegistriesAction, GetContainerRegistriesActionResult],
):
    await test_scenario.test(processors.get_container_registries.wait_for_complete)
