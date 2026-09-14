"""The image node carries the id of the container registry it was pulled from."""

from __future__ import annotations

import uuid
from unittest.mock import AsyncMock, MagicMock

import pytest

from ai.backend.common.data.entity.artifact_registry import ArtifactRegistryID
from ai.backend.common.data.entity.container_registry import ContainerRegistryID
from ai.backend.common.data.entity.image import ImageID
from ai.backend.common.types import ImageCanonical
from ai.backend.manager.api.adapters.image.adapter import ImageAdapter
from ai.backend.manager.data.image.types import (
    ImageData,
    ImageLabelsData,
    ImageResourcesData,
    ImageStatus,
    ImageType,
)
from ai.backend.manager.services.image.actions.search_images import SearchImagesActionResult

REGISTRY_ID = uuid.uuid4()


@pytest.fixture
def image() -> ImageData:
    return ImageData(
        id=ImageID(uuid.uuid4()),
        name=ImageCanonical("cr.backend.ai/stable/python:3.11"),
        project="stable",
        image="python",
        created_at=None,
        tag="3.11",
        registry="cr.backend.ai",
        registry_id=REGISTRY_ID,
        architecture="x86_64",
        config_digest="sha256:abc123",
        size_bytes=1000,
        is_local=False,
        type=ImageType.COMPUTE,
        accelerators=None,
        labels=ImageLabelsData(label_data={}),
        resources=ImageResourcesData(resources_data={}),
        resource_limits=[],
        tags=[],
        status=ImageStatus.ALIVE,
        customized=False,
        creator_id=None,
    )


@pytest.fixture
def processors(image: ImageData) -> MagicMock:
    processors = MagicMock()
    processors.search_images.run = AsyncMock(
        return_value=SearchImagesActionResult(
            data=[image], total_count=1, has_next_page=False, has_previous_page=False
        )
    )
    return processors


@pytest.fixture
def adapter(processors: MagicMock) -> ImageAdapter:
    return ImageAdapter(processors)


async def test_node_carries_a_container_registry_id(
    adapter: ImageAdapter,
    image: ImageData,
) -> None:
    (node,) = await adapter.batch_load_by_ids([image.id])

    assert node is not None
    assert node.registry_id == ContainerRegistryID(REGISTRY_ID)
    assert node.registry_id != ArtifactRegistryID(REGISTRY_ID)
