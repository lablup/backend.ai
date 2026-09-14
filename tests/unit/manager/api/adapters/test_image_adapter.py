"""A cursor handed to the image search pages the list rather than being dropped."""

from __future__ import annotations

import uuid
from unittest.mock import AsyncMock, MagicMock

import pytest

from ai.backend.common.dto.manager.v2.image.request import AdminSearchImagesInput
from ai.backend.manager.api.adapter_options.cursor.cursor import encode_cursor
from ai.backend.manager.api.adapters.image.adapter import ImageAdapter
from ai.backend.manager.models.specs.pagination import CursorForwardPagination
from ai.backend.manager.services.image.actions.search_images import SearchImagesActionResult


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


async def test_admin_search_pages_with_the_cursor_it_is_given(
    adapter: ImageAdapter,
    processors: MagicMock,
) -> None:
    await adapter.admin_search(AdminSearchImagesInput(first=5, after=encode_cursor(uuid.uuid4())))

    action = processors.search_images.run.call_args.args[0]
    assert isinstance(action.querier.pagination, CursorForwardPagination)
    assert action.querier.pagination.cursor_condition is not None
