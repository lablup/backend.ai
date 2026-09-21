"""The image adapter: the DataLoader path answers per image, the REST search reads both paging
modes, and the alias search of one image is scoped to that image."""

from __future__ import annotations

from dataclasses import dataclass
from unittest.mock import AsyncMock, MagicMock
from uuid import uuid4

import pytest

from ai.backend.common.data.entity.image_alias import ImageAliasID
from ai.backend.common.dto.manager.v2.image.request import (
    AdminSearchImagesInput,
    SearchImageAliasesInput,
)
from ai.backend.common.types import ImageCanonical, ImageID
from ai.backend.manager.actions.v2.bulk.result import PartialBulkEntityResult, PartialBulkResult
from ai.backend.manager.actions.v2.ops.result import BatchOpsResult, ScopedFieldsOpsResult
from ai.backend.manager.api.adapter_options.cursor.cursor import encode_cursor
from ai.backend.manager.api.adapters.image.adapter import ImageAdapter
from ai.backend.manager.data.image.types import (
    ImageAliasData,
    ImageData,
    ImageLabelsData,
    ImageResourcesData,
    ImageStatus,
    ImageType,
)
from ai.backend.manager.errors.api import InvalidGraphQLParameters
from ai.backend.manager.errors.common import GenericForbidden
from ai.backend.manager.models.image.scopes import ImageAliasTarget
from ai.backend.manager.models.specs.pagination import (
    CursorBackwardPagination,
    CursorForwardPagination,
    OffsetPagination,
)

READABLE = ImageID(uuid4())
DENIED = ImageID(uuid4())
ABSENT = ImageID(uuid4())
ALIAS = ImageAliasID(uuid4())


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
def alias() -> ImageAliasData:
    return ImageAliasData(id=ALIAS, alias="python")


@pytest.fixture
def denial() -> GenericForbidden:
    return GenericForbidden("no read on this image")


@pytest.fixture
def processors(readable: ImageData, alias: ImageAliasData, denial: GenericForbidden) -> MagicMock:
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
        return_value=BatchOpsResult[ImageData](
            items=[], total_count=0, has_next_page=False, has_previous_page=False
        )
    )
    processors.search_image_aliases.run = AsyncMock(
        return_value=ScopedFieldsOpsResult[ImageAliasData](
            items=[alias], total_count=1, has_next_page=False, has_previous_page=False
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

    pagination = processors.search_images.run.call_args.args[0].searcher.searcher.pagination
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
            input=AdminSearchImagesInput(offset=2),
            expected=OffsetPagination(limit=50, offset=2),
        ),
        _OffsetCase(
            input=AdminSearchImagesInput(),
            expected=OffsetPagination(limit=50, offset=0),
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

    pagination = processors.search_images.run.call_args.args[0].searcher.searcher.pagination
    assert pagination == case.expected


async def test_admin_search_refuses_two_pagination_modes(
    adapter: ImageAdapter,
    processors: MagicMock,
) -> None:
    with pytest.raises(InvalidGraphQLParameters):
        await adapter.admin_search(AdminSearchImagesInput(first=1, limit=1))

    processors.search_images.run.assert_not_awaited()


async def test_scoped_search_aliases_reads_within_the_image(
    adapter: ImageAdapter,
    processors: MagicMock,
) -> None:
    payload = await adapter.scoped_search_aliases(READABLE, SearchImageAliasesInput())

    action = processors.search_image_aliases.run.call_args.args[0]
    assert action.scope_targets() == (READABLE,)
    assert action.operation_scopes() == (ImageAliasTarget(image_id=READABLE),)
    assert [item.alias for item in payload.items] == ["python"]
    assert payload.total_count == 1
