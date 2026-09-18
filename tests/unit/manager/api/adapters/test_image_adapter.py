"""The image adapter: the DataLoader path answers per image, the REST search reads both paging modes."""

from __future__ import annotations

from dataclasses import dataclass
from unittest.mock import AsyncMock, MagicMock
from uuid import uuid4

import pytest

from ai.backend.common.dto.manager.v2.image.request import AdminSearchImagesInput
from ai.backend.common.types import ImageCanonical, ImageID
from ai.backend.manager.actions.v2.bulk.result import PartialBulkEntityResult, PartialBulkResult
from ai.backend.manager.api.adapter_options.cursor.cursor import encode_cursor
from ai.backend.manager.api.adapters.image.adapter import ImageAdapter
from ai.backend.manager.data.image.types import (
    ImageData,
    ImageLabelsData,
    ImageResourcesData,
    ImageStatus,
    ImageType,
)
from ai.backend.manager.errors.api import InvalidGraphQLParameters
from ai.backend.manager.errors.common import GenericForbidden
from ai.backend.manager.models.specs.pagination import (
    CursorBackwardPagination,
    CursorForwardPagination,
    OffsetPagination,
)
from ai.backend.manager.services.image.actions.search_images import SearchImagesActionResult

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
    processors.search_images.run = AsyncMock(
        return_value=SearchImagesActionResult(
            data=[], total_count=0, has_next_page=False, has_previous_page=False
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


@dataclass(frozen=True)
class _CursorCase:
    input: AdminSearchImagesInput
    pagination_type: type[CursorForwardPagination | CursorBackwardPagination]


@pytest.mark.parametrize(
    "case",
    [
        _CursorCase(
            input=AdminSearchImagesInput(first=5, after=encode_cursor(uuid4())),
            pagination_type=CursorForwardPagination,
        ),
        _CursorCase(
            input=AdminSearchImagesInput(last=5, before=encode_cursor(uuid4())),
            pagination_type=CursorBackwardPagination,
        ),
    ],
    ids=lambda case: case.pagination_type.__name__,
)
async def test_admin_search_pages_by_the_cursor_it_is_given(
    case: _CursorCase,
    adapter: ImageAdapter,
    processors: MagicMock,
) -> None:
    await adapter.admin_search(case.input)

    pagination = processors.search_images.run.call_args.args[0].querier.pagination
    assert isinstance(pagination, (CursorForwardPagination, CursorBackwardPagination))
    assert type(pagination) is case.pagination_type
    assert pagination.cursor_condition is not None


@dataclass(frozen=True)
class _OffsetCase:
    input: AdminSearchImagesInput
    expected: OffsetPagination


@pytest.mark.parametrize(
    "case",
    [
        _OffsetCase(
            input=AdminSearchImagesInput(limit=3, offset=2),
            expected=OffsetPagination(limit=3, offset=2),
        ),
        _OffsetCase(
            input=AdminSearchImagesInput(),
            expected=OffsetPagination(limit=10, offset=0),
        ),
    ],
    ids=lambda case: f"limit-{case.expected.limit}-offset-{case.expected.offset}",
)
async def test_admin_search_pages_by_offset(
    case: _OffsetCase,
    adapter: ImageAdapter,
    processors: MagicMock,
) -> None:
    await adapter.admin_search(case.input)

    pagination = processors.search_images.run.call_args.args[0].querier.pagination
    assert pagination == case.expected


async def test_admin_search_refuses_two_pagination_modes(
    adapter: ImageAdapter,
    processors: MagicMock,
) -> None:
    with pytest.raises(InvalidGraphQLParameters):
        await adapter.admin_search(AdminSearchImagesInput(first=1, limit=1))

    processors.search_images.run.assert_not_awaited()
