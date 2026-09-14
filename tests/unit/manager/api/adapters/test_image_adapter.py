"""The image search reads every pagination mode its request type carries."""

from __future__ import annotations

import uuid
from dataclasses import dataclass
from unittest.mock import AsyncMock, MagicMock

import pytest

from ai.backend.common.dto.manager.v2.image.request import AdminSearchImagesInput
from ai.backend.manager.api.adapter_options.cursor.cursor import encode_cursor
from ai.backend.manager.api.adapters.image.adapter import ImageAdapter
from ai.backend.manager.errors.api import InvalidGraphQLParameters
from ai.backend.manager.models.specs.pagination import (
    CursorBackwardPagination,
    CursorForwardPagination,
    OffsetPagination,
    QueryPagination,
)
from ai.backend.manager.services.image.actions.search_images import SearchImagesActionResult


@dataclass(frozen=True)
class _PaginationCase:
    name: str
    input: AdminSearchImagesInput
    expected: type[QueryPagination]


@pytest.fixture
def processors() -> MagicMock:
    processors = MagicMock()
    processors.search_images.run = AsyncMock(
        return_value=SearchImagesActionResult(
            data=[], total_count=0, has_next_page=False, has_previous_page=False
        )
    )
    return processors


@pytest.fixture
def adapter(processors: MagicMock) -> ImageAdapter:
    return ImageAdapter(processors)


@pytest.mark.parametrize(
    "case",
    [
        _PaginationCase(
            name="first",
            input=AdminSearchImagesInput(first=5),
            expected=CursorForwardPagination,
        ),
        _PaginationCase(
            name="first-after",
            input=AdminSearchImagesInput(first=5, after=encode_cursor(uuid.uuid4())),
            expected=CursorForwardPagination,
        ),
        _PaginationCase(
            name="last",
            input=AdminSearchImagesInput(last=5),
            expected=CursorBackwardPagination,
        ),
        _PaginationCase(
            name="last-before",
            input=AdminSearchImagesInput(last=5, before=encode_cursor(uuid.uuid4())),
            expected=CursorBackwardPagination,
        ),
        _PaginationCase(
            name="limit-offset",
            input=AdminSearchImagesInput(limit=5, offset=10),
            expected=OffsetPagination,
        ),
        _PaginationCase(
            name="none",
            input=AdminSearchImagesInput(),
            expected=OffsetPagination,
        ),
    ],
    ids=lambda case: case.name,
)
async def test_admin_search_pages_in_the_mode_the_request_names(
    adapter: ImageAdapter,
    processors: MagicMock,
    case: _PaginationCase,
) -> None:
    await adapter.admin_search(case.input)

    action = processors.search_images.run.call_args.args[0]
    assert isinstance(action.querier.pagination, case.expected)


async def test_admin_search_refuses_two_pagination_modes_at_once(
    adapter: ImageAdapter,
) -> None:
    with pytest.raises(InvalidGraphQLParameters):
        await adapter.admin_search(AdminSearchImagesInput(first=5, limit=5))
