import dataclasses
import uuid

import pytest
from dateutil.parser import isoparse

from ai.backend.common.container_registry import ContainerRegistryType
from ai.backend.manager.models.container_registry import ContainerRegistryRow
from ai.backend.manager.models.image import ImageRow, ImageStatus, ImageType
from ai.backend.manager.services.container_registry.actions.clear_images import (
    ClearImagesAction,
    ClearImagesActionResult,
)
from ai.backend.manager.services.container_registry.processors import ContainerRegistryProcessors
from ai.backend.manager.services.container_registry.service import ContainerRegistryService

from .test_utils import TestScenario

IMAGE_ROW_FIXTURE = ImageRow(
    name="cr.backend.ai/test_project/python:3.9-ubuntu20.04",
    image="test_project/python",
    project="test_project",
    registry="cr.backend.ai",
    registry_id=uuid.UUID("11111111-1111-1111-1111-111111111111"),
    architecture="x86_64",
    accelerators="cuda",
    config_digest="sha256:abcdefgh0123456789abcdefgh0123456789abcdefgh0123456789abcd".ljust(
        72, " "
    ),  # config_digest column is sa.CHAR(length=72)
    size_bytes=12345678,
    is_local=False,
    type=ImageType.COMPUTE,
    labels={},
    resources={},
    status=ImageStatus.ALIVE,
)
IMAGE_ROW_FIXTURE.id = uuid.uuid4()
IMAGE_ROW_FIXTURE.created_at = isoparse("2023-10-01T00:00:00+09:00")

IMAGE_FIXTURE_DATA = IMAGE_ROW_FIXTURE.to_dataclass()

IMAGE_FIXTURE_DICT = dataclasses.asdict(
    dataclasses.replace(IMAGE_FIXTURE_DATA, type=ImageType.COMPUTE._name_, labels={}, resources={})  # type: ignore
)

CONTAINER_REGISTRY_ROW_FIXTURE = ContainerRegistryRow(
    url="https://cr.backend.ai",
    registry_name="cr.backend.ai",
    type=ContainerRegistryType.HARBOR2,
    project="test_project",
    username=None,
    password=None,
    ssl_verify=True,
    is_global=True,
    extra=None,
)

CONTAINER_REGISTRY_ROW_FIXTURE.id = uuid.uuid4()
CONTAINER_REGISTRY_FIXTURE_DATA = CONTAINER_REGISTRY_ROW_FIXTURE.to_dataclass()
CONTAINER_REGISTRY_FIXTURE_DICT = dataclasses.asdict(
    dataclasses.replace(CONTAINER_REGISTRY_FIXTURE_DATA, type=ContainerRegistryType.HARBOR2.value)  # type: ignore
)


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
