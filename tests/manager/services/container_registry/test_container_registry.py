import uuid

import pytest
from aioresponses import aioresponses

from ai.backend.common.types import SlotName
from ai.backend.manager.data.image.types import (
    ImageData,
    ImageLabelsData,
    ImageResourcesData,
    ImageStatus,
    ImageType,
)
from ai.backend.manager.services.container_registry.actions.clear_images import (
    ClearImagesAction,
    ClearImagesActionResult,
)
from ai.backend.manager.services.container_registry.actions.rescan_images import (
    RescanImagesAction,
    RescanImagesActionResult,
)
from ai.backend.manager.services.container_registry.processors import ContainerRegistryProcessors
from ai.backend.manager.services.container_registry.service import ContainerRegistryService
from ai.backend.testutils.mock import mock_aioresponses_sequential_payloads, setup_dockerhub_mocking

from ..fixtures import (
    CONTAINER_REGISTRY_FIXTURE_DATA,
    CONTAINER_REGISTRY_FIXTURE_DICT,
    CONTAINER_REGISTRY_ROW_FIXTURE,
    IMAGE_FIXTURE_DICT,
)
from ..test_utils import TestScenario


@pytest.fixture
def processors(extra_fixtures, database_fixture, database_engine):
    container_registry_service = ContainerRegistryService(
        db=database_engine,
    )
    return ContainerRegistryProcessors(container_registry_service, [])


@pytest.mark.asyncio
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


EXPECTED_IMAGE_RESCAN_RESULT = [
    ImageData(
        id=uuid.uuid4(),
        name="registry.example.com/test_project/python:latest",
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
            TestScenario.success(
                "Rescan all projects",
                RescanImagesAction(
                    registry=CONTAINER_REGISTRY_ROW_FIXTURE.registry_name,
                    project=None,
                    progress_reporter=None,
                ),
                RescanImagesActionResult(
                    images=EXPECTED_IMAGE_RESCAN_RESULT,
                    registry=CONTAINER_REGISTRY_FIXTURE_DATA,
                    errors=[],
                ),
            ),
            {
                "get_token": {"token": "fake-token"},
                "get_catalog": {
                    "repositories": [
                        "test_project/python",
                        "other/dangling-image1",
                        "other/dangling-image2",
                        "other/python",
                    ],
                },
                "get_tags": mock_aioresponses_sequential_payloads([
                    {"tags": ["latest"]},
                    {"tags": []},
                    {"tags": None},
                    {"tags": ["latest"]},
                ]),
                "get_manifest": {
                    "schemaVersion": 2,
                    "mediaType": "application/vnd.docker.distribution.manifest.v2+json",
                    "config": {
                        "mediaType": "application/vnd.docker.container.image.v1+json",
                        "size": 100,
                        "digest": "sha256:1111111111111111111111111111111111111111111111111111111111111111",
                    },
                    "layers": [],
                },
                "get_config": {"architecture": "amd64", "os": "linux"},
            },
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
    extra_fixtures,
    processors: ContainerRegistryProcessors,
    test_scenario: TestScenario[RescanImagesAction, RescanImagesActionResult],
):
    with aioresponses() as mocked:
        registry_url = CONTAINER_REGISTRY_FIXTURE_DATA.url
        setup_dockerhub_mocking(mocked, registry_url, dockerhub_responses_mock)

        await test_scenario.test(processors.rescan_images.wait_for_complete)
