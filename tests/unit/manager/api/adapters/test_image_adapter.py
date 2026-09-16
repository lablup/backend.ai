"""The image DataLoader path: each image is answered for."""

from __future__ import annotations

from unittest.mock import AsyncMock, MagicMock
from uuid import uuid4

import pytest

from ai.backend.common.types import ImageCanonical, ImageID
from ai.backend.manager.actions.v2.bulk.result import PartialBulkEntityResult, PartialBulkResult
from ai.backend.manager.api.adapters.image.adapter import ImageAdapter
from ai.backend.manager.data.image.types import (
    ImageData,
    ImageLabelsData,
    ImageResourcesData,
    ImageStatus,
    ImageType,
)
from ai.backend.manager.errors.common import GenericForbidden

READABLE = ImageID(uuid4())
DENIED = ImageID(uuid4())
ABSENT = ImageID(uuid4())


@pytest.fixture
def readable() -> ImageData:
    return ImageData(
        id=READABLE,
        name=ImageCanonical("registry.test.local/test/python:3.13"),
        project="test",
        image="test/python",
        created_at=None,
        tag="3.13",
        registry="registry.test.local",
        registry_id=uuid4(),
        architecture="x86_64",
        config_digest="sha256:0",
        size_bytes=0,
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
def denial() -> GenericForbidden:
    return GenericForbidden("no read on this image")


@pytest.fixture
def processors(readable: ImageData, denial: GenericForbidden) -> MagicMock:
    processors = MagicMock()
    processors.bulk_get.run = AsyncMock(
        return_value=PartialBulkResult(
            items=[
                PartialBulkEntityResult[ImageData].succeeded(READABLE, readable),
                PartialBulkEntityResult[ImageData].denied(DENIED, denial),
                PartialBulkEntityResult[ImageData].nothing(ABSENT),
            ]
        )
    )
    return processors


@pytest.fixture
def adapter(processors: MagicMock) -> ImageAdapter:
    return ImageAdapter(processors)


async def test_batch_load_answers_per_id(
    adapter: ImageAdapter,
    denial: GenericForbidden,
) -> None:
    node, refused, missing = await adapter.batch_load_by_ids([READABLE, DENIED, ABSENT])

    assert node is not None and not isinstance(node, Exception)
    assert node.id == READABLE
    assert refused is denial
    assert missing is None


async def test_no_ids_read_nothing(adapter: ImageAdapter, processors: MagicMock) -> None:
    assert await adapter.batch_load_by_ids([]) == []
    processors.bulk_get.run.assert_not_awaited()
