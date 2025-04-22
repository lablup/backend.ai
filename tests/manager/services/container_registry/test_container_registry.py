import pytest

from ai.backend.manager.services.container_registry.actions.clear_images import (
    ClearImagesAction,
    ClearImagesActionResult,
)
from ai.backend.manager.services.container_registry.processors import ContainerRegistryProcessors
from ai.backend.manager.services.container_registry.service import ContainerRegistryService

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


# @pytest.mark.timeout(60)
# @pytest.mark.parametrize(
#     ("test_scenario", "mock_dockerhub_responses"),
#     [
#         (
#             TestScenario.success(
#                 "Success – all projects",
#                 RescanImagesAction(
#                     registry=CONTAINER_REGISTRY_ROW_FIXTURE.registry_name,
#                     project=None,
#                     progress_reporter=None,
#                 ),
#                 RescanImagesActionResult(
#                     images={("test_project/python", "latest"),
#                             ("other/python", "latest")},
#                     registry=CONTAINER_REGISTRY_FIXTURE_DATA,
#                     errors=[],
#                 ),
#             ),
#             {
#                 "get_token": {"token": "fake-token"},
#                 "get_catalog": {
#                     "repositories": [
#                         "test_project/python",
#                         "other/dangling-image1",
#                         "other/dangling-image2",
#                         "other/python",
#                     ],
#                 },
#                 "get_tags": mock_aioresponses_sequential_payloads([
#                     {"tags": ["latest"]},
#                     {"tags": []},
#                     {"tags": None},
#                     {"tags": ["latest"]},
#                 ]),
#                 "get_manifest": {
#                     "schemaVersion": 2,
#                     "mediaType": "application/vnd.docker.distribution.manifest.v2+json",
#                     "config": {
#                         "mediaType": "application/vnd.docker.container.image.v1+json",
#                         "size": 100,
#                         "digest": "sha256:1111111111111111111111111111111111111111111111111111111111111111",
#                     },
#                     "layers": [],
#                 },
#                 "get_config": {"architecture": "amd64", "os": "linux"},
#             },
#         ),

#         (
#             TestScenario.success(
#                 "Success – specific project",
#                 RescanImagesAction(
#                     registry=CONTAINER_REGISTRY_ROW_FIXTURE.registry_name,
#                     project=CONTAINER_REGISTRY_ROW_FIXTURE.project,
#                     progress_reporter=None,
#                 ),
#                 RescanImagesActionResult(
#                     images={("test_project/python", "latest")},
#                     registry=CONTAINER_REGISTRY_FIXTURE_DATA,
#                     errors=[],
#                 ),
#             ),
#             {
#                 "get_token": {"token": "fake-token"},
#                 "get_catalog": {
#                     "repositories": ["test_project/python", "other/python"],
#                 },
#                 "get_tags": {"tags": ["latest"]},
#                 "get_manifest": {
#                     "schemaVersion": 2,
#                     "mediaType": "application/vnd.docker.distribution.manifest.v2+json",
#                     "config": {
#                         "mediaType": "application/vnd.docker.container.image.v1+json",
#                         "size": 100,
#                         "digest": "sha256:1111111111111111111111111111111111111111111111111111111111111111",
#                     },
#                     "layers": [],
#                 },
#                 "get_config": {"architecture": "amd64", "os": "linux"},
#             },
#         ),
#     ],
#     ids=[
#         "Rescan all project",
#         "Rescan specific project",
#     ],
# )
# @pytest.mark.parametrize(
#     "extra_fixtures",
#     [
#         {
#             "container_registries": [
#                 CONTAINER_REGISTRY_FIXTURE_DICT,
#             ],
#         }
#     ],
# )
# async def test_rescan_images(
#     test_case,
#     extra_fixtures,
#     processors: ContainerRegistryProcessors,
#     test_scenario: TestScenario[RescanImagesAction, RescanImagesActionResult],
# ):
#     with aioresponses() as mocked:
#         mock_dockerhub_responses = test_case["mock_dockerhub_responses"]
#         registry_url = extra_fixtures["container_registries"][0]["url"]
#         setup_dockerhub_mocking(mocked, registry_url, mock_dockerhub_responses)

#         await test_scenario.test(processors.rescan_images.wait_for_complete)
