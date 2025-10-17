import uuid

import pytest
from aioresponses import aioresponses

from ai.backend.common.types import ImageCanonical, ImageID, SlotName
from ai.backend.manager.data.image.types import (
    ImageData,
    ImageLabelsData,
    ImageResourcesData,
    ImageStatus,
    ImageType,
)
from ai.backend.manager.services.container_registry.actions.rescan_images import (
    RescanImagesAction,
    RescanImagesActionResult,
)
from ai.backend.manager.services.container_registry.processors import ContainerRegistryProcessors
from ai.backend.testutils.mock import setup_dockerhub_mocking

from ...fixtures import (
    CONTAINER_REGISTRY_FIXTURE_DATA,
    CONTAINER_REGISTRY_FIXTURE_DICT,
    CONTAINER_REGISTRY_ROW_FIXTURE,
    DOCKERHUB_RESPONSE_MOCK,
)
from ...utils import ScenarioBase

# Added some default values to IMAGE_FIXTURE_DATA
EXPECTED_IMAGE_RESCAN_RESULT = [
    ImageData(
        id=ImageID(uuid.uuid4()),
        name=ImageCanonical("registry.example.com/test_project/python:latest"),
        project="test_project",
        image="test_project/python",
        created_at=None,
        tag="latest",
        registry="registry.example.com",
        registry_id=CONTAINER_REGISTRY_ROW_FIXTURE.id,
        architecture="x86_64",
        config_digest="sha256:1111111111111111111111111111111111111111111111111111111111111111",
        size_bytes=100,
        is_local=False,
        type=ImageType.COMPUTE,
        accelerators="*",
        labels=ImageLabelsData(
            label_data={},
        ),
        resources=ImageResourcesData(
            resources_data={
                SlotName("cpu"): {
                    "max": None,
                    "min": "1",
                },
                SlotName("mem"): {
                    "max": None,
                    "min": "1073741824",
                },
            },
        ),
        status=ImageStatus.ALIVE,
    ),
]


@pytest.mark.timeout(60)
@pytest.mark.parametrize(
    ("test_scenario", "dockerhub_responses_mock"),
    [
        (
            ScenarioBase.success(
                "Success Case",
                RescanImagesAction(
                    registry=CONTAINER_REGISTRY_ROW_FIXTURE.registry_name,
                    project=CONTAINER_REGISTRY_ROW_FIXTURE.project,
                    progress_reporter=None,
                ),
                RescanImagesActionResult(
                    images=EXPECTED_IMAGE_RESCAN_RESULT,
                    registry=CONTAINER_REGISTRY_FIXTURE_DATA,
                    errors=[],
                ),
            ),
            DOCKERHUB_RESPONSE_MOCK,
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
async def test_rescan_images(
    dockerhub_responses_mock,
    processors: ContainerRegistryProcessors,
    test_scenario: ScenarioBase[RescanImagesAction, RescanImagesActionResult],
):
    with aioresponses() as mocked:
        registry_url = CONTAINER_REGISTRY_FIXTURE_DATA.url
        setup_dockerhub_mocking(mocked, registry_url, dockerhub_responses_mock)

        await test_scenario.test(processors.rescan_images.wait_for_complete)


@pytest.mark.timeout(60)
@pytest.mark.rescan_cr_backend_ai
async def test_rescan_images_on_cr_backend_ai(
    processors: ContainerRegistryProcessors,
):
    """
    Test rescan images on cr.backend.ai registry.
    Use this test optionally to perform an actual rescan test in the actual registry.

    To include this test in the pants test, add `--rescan-cr-backend-ai` to the pytest args.
    """
    result = await processors.rescan_images.wait_for_complete(
        RescanImagesAction(
            registry="cr.backend.ai",
            project="stable",
            progress_reporter=None,
        )
    )

    assert len(result.images) > 0, "No images found in the registry"
    assert len(result.errors) == 0, "Errors found during rescan"
