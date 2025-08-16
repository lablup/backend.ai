import copy
import dataclasses
import uuid

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
from ...utils import ScenarioBase

CONTAINER_REGISTRY_FIXTURE_2_DATA = copy.deepcopy(CONTAINER_REGISTRY_FIXTURE_DATA)
CONTAINER_REGISTRY_FIXTURE_2_DATA.id = uuid.uuid4()
CONTAINER_REGISTRY_FIXTURE_2_DATA.project = "test_project2"

CONTAINER_REGISTRY_FIXTURE_2_DICT = dataclasses.asdict(CONTAINER_REGISTRY_FIXTURE_2_DATA)


@pytest.mark.parametrize(
    "test_scenario",
    [
        ScenarioBase.success(
            "Load container registries with registry name",
            LoadContainerRegistriesAction(
                registry=CONTAINER_REGISTRY_ROW_FIXTURE.registry_name, project=None
            ),
            LoadContainerRegistriesActionResult(
                registries=[
                    CONTAINER_REGISTRY_FIXTURE_DATA,
                    CONTAINER_REGISTRY_FIXTURE_2_DATA,
                ]
            ),
        ),
        ScenarioBase.success(
            "Load container registries with registry name and project",
            LoadContainerRegistriesAction(
                registry=CONTAINER_REGISTRY_ROW_FIXTURE.registry_name,
                project=CONTAINER_REGISTRY_ROW_FIXTURE.project,
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
                CONTAINER_REGISTRY_FIXTURE_2_DICT,
            ],
        }
    ],
)
async def test_load_container_registries(
    processors: ContainerRegistryProcessors,
    test_scenario: ScenarioBase[LoadContainerRegistriesAction, LoadContainerRegistriesActionResult],
):
    await test_scenario.test(processors.load_container_registries.wait_for_complete)
