import pytest

from ai.backend.manager.data.container_registry.types import (
    ContainerRegistryLocationInfo,
)
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
                registries=[
                    # fixtures from example-container-registries-harbor.json
                    # Sorted by registry_name first (cr.backend.ai < registry.example.com),
                    # then by project (community < multiarch < stable)
                    ContainerRegistryLocationInfo(
                        project="community",
                        registry_name="cr.backend.ai",
                        url="https://cr.backend.ai/",
                    ),
                    ContainerRegistryLocationInfo(
                        project="multiarch",
                        registry_name="cr.backend.ai",
                        url="https://cr.backend.ai/",
                    ),
                    ContainerRegistryLocationInfo(
                        project="stable",
                        registry_name="cr.backend.ai",
                        url="https://cr.backend.ai/",
                    ),
                    # fixtures from fixtures.py
                    ContainerRegistryLocationInfo(
                        project="test_project",
                        registry_name="registry.example.com",
                        url="https://registry.example.com/",
                    ),
                ],
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
