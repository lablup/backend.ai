"""The login client type adapter: the search reads both paging modes it advertises."""

from __future__ import annotations

from dataclasses import dataclass
from unittest.mock import AsyncMock, MagicMock
from uuid import uuid4

import pytest

from ai.backend.common.dto.manager.defs import DEFAULT_PAGE_LIMIT
from ai.backend.common.dto.manager.v2.login_client_type.request import (
    SearchLoginClientTypesInput,
)
from ai.backend.manager.actions.v2.ops.result import BatchOpsResult
from ai.backend.manager.api.adapter_options.cursor.cursor import encode_cursor
from ai.backend.manager.api.adapters.login_client_type.adapter import LoginClientTypeAdapter
from ai.backend.manager.errors.api import InvalidGraphQLParameters
from ai.backend.manager.models.specs.pagination import (
    CursorBackwardPagination,
    CursorForwardPagination,
    OffsetPagination,
)


@pytest.fixture
def processors() -> MagicMock:
    processors = MagicMock()
    processors.public_search.run = AsyncMock(
        return_value=BatchOpsResult(
            items=[], total_count=0, has_next_page=False, has_previous_page=False
        )
    )
    return processors


@pytest.fixture
def adapter(processors: MagicMock) -> LoginClientTypeAdapter:
    return LoginClientTypeAdapter(processors)


@dataclass(frozen=True)
class _CursorCase:
    input: SearchLoginClientTypesInput
    pagination_type: type[CursorForwardPagination | CursorBackwardPagination]


@pytest.mark.parametrize(
    "case",
    [
        _CursorCase(
            input=SearchLoginClientTypesInput(first=5, after=encode_cursor(uuid4())),
            pagination_type=CursorForwardPagination,
        ),
        _CursorCase(
            input=SearchLoginClientTypesInput(last=5, before=encode_cursor(uuid4())),
            pagination_type=CursorBackwardPagination,
        ),
    ],
    ids=lambda case: case.pagination_type.__name__,
)
async def test_search_pages_by_the_cursor_it_is_given(
    case: _CursorCase,
    adapter: LoginClientTypeAdapter,
    processors: MagicMock,
) -> None:
    await adapter.search(case.input)

    pagination = processors.public_search.run.call_args.args[0].searcher.pagination
    assert isinstance(pagination, (CursorForwardPagination, CursorBackwardPagination))
    assert type(pagination) is case.pagination_type
    assert pagination.cursor_condition is not None


@dataclass(frozen=True)
class _OffsetCase:
    input: SearchLoginClientTypesInput
    expected: OffsetPagination


@pytest.mark.parametrize(
    "case",
    [
        _OffsetCase(
            input=SearchLoginClientTypesInput(limit=3, offset=2),
            expected=OffsetPagination(limit=3, offset=2),
        ),
        _OffsetCase(
            input=SearchLoginClientTypesInput(offset=2),
            expected=OffsetPagination(limit=DEFAULT_PAGE_LIMIT, offset=2),
        ),
        _OffsetCase(
            input=SearchLoginClientTypesInput(),
            expected=OffsetPagination(limit=DEFAULT_PAGE_LIMIT, offset=0),
        ),
    ],
    ids=lambda case: f"limit-{case.expected.limit}-offset-{case.expected.offset}",
)
async def test_search_pages_by_offset(
    case: _OffsetCase,
    adapter: LoginClientTypeAdapter,
    processors: MagicMock,
) -> None:
    await adapter.search(case.input)

    pagination = processors.public_search.run.call_args.args[0].searcher.pagination
    assert pagination == case.expected


async def test_search_refuses_two_pagination_modes(
    adapter: LoginClientTypeAdapter,
    processors: MagicMock,
) -> None:
    with pytest.raises(InvalidGraphQLParameters):
        await adapter.search(SearchLoginClientTypesInput(first=1, limit=1))

    processors.public_search.run.assert_not_awaited()
