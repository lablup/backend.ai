"""Tests for the pagination mode a PaginationOptions names."""

from __future__ import annotations

from dataclasses import dataclass

import pytest

from ai.backend.manager.api.adapter_options.pagination.pagination import PaginationOptions


@dataclass(frozen=True)
class _ModeCase:
    name: str
    options: PaginationOptions
    has_forward_cursor: bool
    has_backward_cursor: bool
    has_offset: bool


@pytest.mark.parametrize(
    "case",
    [
        _ModeCase("nothing", PaginationOptions(), False, False, False),
        _ModeCase("first", PaginationOptions(first=5), True, False, False),
        _ModeCase("after", PaginationOptions(after="c"), True, False, False),
        _ModeCase("last", PaginationOptions(last=5), False, True, False),
        _ModeCase("before", PaginationOptions(before="c"), False, True, False),
        _ModeCase("limit", PaginationOptions(limit=5), False, False, True),
        _ModeCase("offset", PaginationOptions(offset=5), False, False, True),
        _ModeCase("first-and-limit", PaginationOptions(first=5, limit=5), True, False, True),
    ],
    ids=lambda case: case.name,
)
def test_the_mode_the_options_name(case: _ModeCase) -> None:
    assert case.options.has_forward_cursor is case.has_forward_cursor
    assert case.options.has_backward_cursor is case.has_backward_cursor
    assert case.options.has_cursor is (case.has_forward_cursor or case.has_backward_cursor)
    assert case.options.has_offset is case.has_offset
