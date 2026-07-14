"""Tests for repository base types including pagination classes."""

from __future__ import annotations

from typing import Any, cast
from unittest.mock import MagicMock

import pytest
import sqlalchemy as sa
from sqlalchemy import Row

from ai.backend.manager.repositories.base import (
    CursorBackwardPagination,
    CursorForwardPagination,
    NoPagination,
    OffsetPagination,
    PageInfoResult,
)


class TestOffsetPagination:
    """Tests for OffsetPagination class."""

    def test_apply_with_limit_only(self) -> None:
        """Test that apply() correctly applies limit to query."""
        pagination = OffsetPagination(limit=10)
        mock_query = MagicMock()
        mock_query.limit.return_value = mock_query

        result = pagination.apply(mock_query)

        mock_query.limit.assert_called_once_with(10)
        # offset should not be called when offset is 0
        mock_query.offset.assert_not_called()
        assert result is mock_query

    def test_apply_with_limit_and_offset(self) -> None:
        """Test that apply() correctly applies both limit and offset."""
        pagination = OffsetPagination(limit=10, offset=20)
        mock_query = MagicMock()
        mock_query.limit.return_value = mock_query
        mock_query.offset.return_value = mock_query

        result = pagination.apply(mock_query)

        mock_query.limit.assert_called_once_with(10)
        mock_query.offset.assert_called_once_with(20)
        assert result is mock_query

    def test_compute_page_info_has_next_and_previous(self) -> None:
        """Test page info when there are more pages in both directions."""
        pagination = OffsetPagination(limit=10, offset=10)
        rows = [MagicMock() for _ in range(10)]

        result = pagination.compute_page_info(cast(list[Row[Any]], rows), total_count=30)

        assert isinstance(result, PageInfoResult)
        assert result.rows == rows
        assert result.has_previous_page is True  # offset > 0
        assert result.has_next_page is True  # 10 + 10 < 30

    def test_compute_page_info_no_previous(self) -> None:
        """Test page info at the beginning (offset=0)."""
        pagination = OffsetPagination(limit=10, offset=0)
        rows = [MagicMock() for _ in range(10)]

        result = pagination.compute_page_info(cast(list[Row[Any]], rows), total_count=20)

        assert result.has_previous_page is False  # offset is 0
        assert result.has_next_page is True  # 0 + 10 < 20

    def test_compute_page_info_no_next(self) -> None:
        """Test page info at the end (no more items)."""
        pagination = OffsetPagination(limit=10, offset=20)
        rows = [MagicMock() for _ in range(5)]

        result = pagination.compute_page_info(cast(list[Row[Any]], rows), total_count=25)

        assert result.has_previous_page is True  # offset > 0
        assert result.has_next_page is False  # 20 + 5 >= 25


class TestCursorForwardPagination:
    """Tests for CursorForwardPagination class."""

    @pytest.fixture
    def mock_cursor_condition(self) -> MagicMock:
        """Create a mock cursor condition that returns a SQLAlchemy expression."""
        mock = MagicMock()
        mock.return_value = sa.literal(True)
        return mock

    @pytest.fixture
    def mock_cursor_order(self) -> Any:
        """Create a mock cursor order."""
        return MagicMock(spec=sa.sql.ClauseElement)

    def test_apply(
        self,
        mock_cursor_condition: MagicMock,
        mock_cursor_order: Any,
    ) -> None:
        """Test that apply() applies cursor_condition, cursor_order, and limit+1."""
        pagination = CursorForwardPagination(
            first=10,
            cursor_condition=mock_cursor_condition,
            cursor_order=mock_cursor_order,
        )

        mock_query = MagicMock()
        mock_query.where.return_value = mock_query
        mock_query.order_by.return_value = mock_query
        mock_query.limit.return_value = mock_query

        result = pagination.apply(mock_query)

        # cursor_condition should be called
        mock_cursor_condition.assert_called_once()
        # where should be called with the result of cursor_condition
        mock_query.where.assert_called_once()
        # order_by should be called with cursor_order
        mock_query.order_by.assert_called_once_with(mock_cursor_order)
        # limit should be first + 1 (for has_next_page detection)
        mock_query.limit.assert_called_once_with(11)
        assert result is mock_query

    def test_compute_page_info_has_next(
        self,
        mock_cursor_condition: MagicMock,
        mock_cursor_order: Any,
    ) -> None:
        """Test page info when there are more pages (rows > first)."""
        pagination = CursorForwardPagination(
            first=10,
            cursor_condition=mock_cursor_condition,
            cursor_order=mock_cursor_order,
        )
        # 11 rows returned means there's a next page
        rows = [MagicMock() for _ in range(11)]

        result = pagination.compute_page_info(cast(list[Row[Any]], rows), _total_count=100)

        assert result.has_next_page is True
        assert result.has_previous_page is True  # cursor exists = has previous
        # Should slice to only first 10
        assert len(result.rows) == 10

    def test_compute_page_info_no_next(
        self,
        mock_cursor_condition: MagicMock,
        mock_cursor_order: Any,
    ) -> None:
        """Test page info when there are no more pages (rows <= first)."""
        pagination = CursorForwardPagination(
            first=10,
            cursor_condition=mock_cursor_condition,
            cursor_order=mock_cursor_order,
        )
        # Exactly 10 rows means no next page
        rows = [MagicMock() for _ in range(10)]

        result = pagination.compute_page_info(cast(list[Row[Any]], rows), _total_count=100)

        assert result.has_next_page is False
        assert result.has_previous_page is True  # cursor exists = has previous
        assert len(result.rows) == 10

    def test_compute_page_info_always_has_previous(
        self,
        mock_cursor_condition: MagicMock,
        mock_cursor_order: Any,
    ) -> None:
        """Test that cursor-based pagination always indicates has_previous_page=True."""
        pagination = CursorForwardPagination(
            first=10,
            cursor_condition=mock_cursor_condition,
            cursor_order=mock_cursor_order,
        )
        rows = [MagicMock() for _ in range(5)]

        result = pagination.compute_page_info(cast(list[Row[Any]], rows), _total_count=5)

        # When using cursor, there's always a previous page (we came from somewhere)
        assert result.has_previous_page is True


class TestCursorBackwardPagination:
    """Tests for CursorBackwardPagination class."""

    @pytest.fixture
    def mock_cursor_condition(self) -> MagicMock:
        """Create a mock cursor condition that returns a SQLAlchemy expression."""
        mock = MagicMock()
        mock.return_value = sa.literal(True)
        return mock

    @pytest.fixture
    def mock_cursor_order(self) -> Any:
        """Create a mock cursor order."""
        return MagicMock(spec=sa.sql.ClauseElement)

    def test_apply(
        self,
        mock_cursor_condition: MagicMock,
        mock_cursor_order: Any,
    ) -> None:
        """Test that apply() applies cursor_condition, cursor_order, and limit+1."""
        pagination = CursorBackwardPagination(
            last=10,
            cursor_condition=mock_cursor_condition,
            cursor_order=mock_cursor_order,
        )

        mock_query = MagicMock()
        mock_query.where.return_value = mock_query
        mock_query.order_by.return_value = mock_query
        mock_query.limit.return_value = mock_query

        result = pagination.apply(mock_query)

        # cursor_condition should be called
        mock_cursor_condition.assert_called_once()
        # where should be called with the result of cursor_condition
        mock_query.where.assert_called_once()
        # order_by should be called with cursor_order
        mock_query.order_by.assert_called_once_with(mock_cursor_order)
        # limit should be last + 1 (for has_previous_page detection)
        mock_query.limit.assert_called_once_with(11)
        assert result is mock_query

    def test_compute_page_info_has_previous(
        self,
        mock_cursor_condition: MagicMock,
        mock_cursor_order: Any,
    ) -> None:
        """Test page info when there are more pages before (rows > last)."""
        pagination = CursorBackwardPagination(
            last=10,
            cursor_condition=mock_cursor_condition,
            cursor_order=mock_cursor_order,
        )
        # 11 rows returned means there's a previous page
        rows = [MagicMock() for _ in range(11)]

        result = pagination.compute_page_info(cast(list[Row[Any]], rows), _total_count=100)

        assert result.has_previous_page is True
        assert result.has_next_page is True  # cursor exists = has next
        # Should slice to only first 10
        assert len(result.rows) == 10

    def test_compute_page_info_no_previous(
        self,
        mock_cursor_condition: MagicMock,
        mock_cursor_order: Any,
    ) -> None:
        """Test page info when there are no more pages before (rows <= last)."""
        pagination = CursorBackwardPagination(
            last=10,
            cursor_condition=mock_cursor_condition,
            cursor_order=mock_cursor_order,
        )
        # Exactly 10 rows means no previous page
        rows = [MagicMock() for _ in range(10)]

        result = pagination.compute_page_info(cast(list[Row[Any]], rows), _total_count=100)

        assert result.has_previous_page is False
        assert result.has_next_page is True  # cursor exists = has next
        assert len(result.rows) == 10

    def test_compute_page_info_always_has_next(
        self,
        mock_cursor_condition: MagicMock,
        mock_cursor_order: Any,
    ) -> None:
        """Test that backward cursor pagination always indicates has_next_page=True."""
        pagination = CursorBackwardPagination(
            last=10,
            cursor_condition=mock_cursor_condition,
            cursor_order=mock_cursor_order,
        )
        rows = [MagicMock() for _ in range(5)]

        result = pagination.compute_page_info(cast(list[Row[Any]], rows), _total_count=5)

        # When using backward cursor, there's always a next page (we came from somewhere ahead)
        assert result.has_next_page is True


class TestCountStrategyMethods:
    """Tests for the polymorphic count strategy: attach_count() and count_from_rows()."""

    def test_offset_attach_count_adds_column(self) -> None:
        """OffsetPagination.attach_count() folds a count column into the query."""
        pagination = OffsetPagination(limit=10)
        mock_query = MagicMock()
        mock_query.add_columns.return_value = mock_query

        result = pagination.attach_count(mock_query)

        mock_query.add_columns.assert_called_once()
        assert result is mock_query

    def test_offset_count_from_rows_reads_window_value(self) -> None:
        """OffsetPagination.count_from_rows() reads total_count from the first row."""
        pagination = OffsetPagination(limit=10)
        rows = [MagicMock(total_count=42) for _ in range(3)]

        assert pagination.count_from_rows(cast(list[Row[Any]], rows)) == 42

    def test_offset_count_from_rows_empty_returns_none(self) -> None:
        """OffsetPagination.count_from_rows() returns None on empty rows (fallback)."""
        pagination = OffsetPagination(limit=10)

        assert pagination.count_from_rows([]) is None

    def test_no_pagination_attach_count_is_identity(self) -> None:
        """NoPagination.attach_count() leaves the query unchanged."""
        pagination = NoPagination()
        mock_query = MagicMock()

        result = pagination.attach_count(mock_query)

        mock_query.add_columns.assert_not_called()
        assert result is mock_query

    def test_no_pagination_count_from_rows_is_len(self) -> None:
        """NoPagination.count_from_rows() returns len(rows), never None."""
        pagination = NoPagination()
        rows = [MagicMock() for _ in range(7)]

        assert pagination.count_from_rows(cast(list[Row[Any]], rows)) == 7
        assert pagination.count_from_rows([]) == 0

    def test_cursor_forward_attach_count_is_identity(self) -> None:
        """CursorForwardPagination.attach_count() leaves the query unchanged."""
        pagination = CursorForwardPagination(first=10, cursor_order=MagicMock())
        mock_query = MagicMock()

        result = pagination.attach_count(mock_query)

        mock_query.add_columns.assert_not_called()
        assert result is mock_query

    def test_cursor_forward_count_from_rows_returns_none(self) -> None:
        """CursorForwardPagination.count_from_rows() always signals a count query."""
        pagination = CursorForwardPagination(first=10, cursor_order=MagicMock())
        rows = [MagicMock() for _ in range(11)]

        assert pagination.count_from_rows(cast(list[Row[Any]], rows)) is None

    def test_cursor_backward_attach_count_is_identity(self) -> None:
        """CursorBackwardPagination.attach_count() leaves the query unchanged."""
        pagination = CursorBackwardPagination(last=10, cursor_order=MagicMock())
        mock_query = MagicMock()

        result = pagination.attach_count(mock_query)

        mock_query.add_columns.assert_not_called()
        assert result is mock_query

    def test_cursor_backward_count_from_rows_returns_none(self) -> None:
        """CursorBackwardPagination.count_from_rows() always signals a count query."""
        pagination = CursorBackwardPagination(last=10, cursor_order=MagicMock())
        rows = [MagicMock() for _ in range(11)]

        assert pagination.count_from_rows(cast(list[Row[Any]], rows)) is None
