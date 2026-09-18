"""The image adapter: the REST search reads both paging modes."""

from __future__ import annotations

from dataclasses import dataclass
from unittest.mock import AsyncMock, MagicMock
from uuid import uuid4

import pytest

from ai.backend.common.dto.manager.v2.image.request import AdminSearchImagesInput
from ai.backend.manager.api.adapter_options.cursor.cursor import encode_cursor
from ai.backend.manager.api.adapters.image.adapter import ImageAdapter
from ai.backend.manager.errors.api import InvalidGraphQLParameters
from ai.backend.manager.repositories.base.pagination import (
    CursorBackwardPagination,
    CursorForwardPagination,
    OffsetPagination,
)
from ai.backend.manager.services.image.actions.search_images import SearchImagesActionResult


@pytest.fixture
def processors() -> MagicMock:
    processors = MagicMock()
    processors.image.search_images.wait_for_complete = AsyncMock(
        return_value=SearchImagesActionResult(
            data=[], total_count=0, has_next_page=False, has_previous_page=False
        )
    )
    return processors


@pytest.fixture
def adapter(processors: MagicMock) -> ImageAdapter:
    return ImageAdapter(processors)


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

    action = processors.image.search_images.wait_for_complete.call_args.args[0]
    pagination = action.querier.pagination
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

    action = processors.image.search_images.wait_for_complete.call_args.args[0]
    assert action.querier.pagination == case.expected


async def test_admin_search_refuses_two_pagination_modes(
    adapter: ImageAdapter,
    processors: MagicMock,
) -> None:
    with pytest.raises(InvalidGraphQLParameters):
        await adapter.admin_search(AdminSearchImagesInput(first=1, limit=1))

    processors.image.search_images.wait_for_complete.assert_not_awaited()
