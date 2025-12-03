"""Tests for GraphQL adapter utilities including pagination building."""

from __future__ import annotations

from typing import Any
from unittest.mock import MagicMock

import pytest

from ai.backend.manager.api.gql.adapter import DEFAULT_PAGINATION_LIMIT, BaseGQLAdapter
from ai.backend.manager.api.gql.base import encode_cursor
from ai.backend.manager.errors.api import InvalidGraphQLParameters
from ai.backend.manager.repositories.base import (
    CursorBackwardPagination,
    CursorForwardPagination,
    OffsetPagination,
)


class TestBaseGQLAdapterBuildPagination:
    """Tests for BaseGQLAdapter.build_pagination method."""

    @pytest.fixture
    def adapter(self) -> BaseGQLAdapter:
        """Create a BaseGQLAdapter instance."""
        return BaseGQLAdapter()

    @pytest.fixture
    def mock_cursor_factory(self) -> MagicMock:
        """Create a mock cursor condition factory."""
        factory = MagicMock()
        factory.return_value = MagicMock()  # Return a mock QueryCondition
        return factory

    @pytest.fixture
    def mock_order(self) -> Any:
        """Create a mock default order."""
        return MagicMock()

    def test_build_pagination_forward_cursor(
        self,
        adapter: BaseGQLAdapter,
        mock_cursor_factory: MagicMock,
        mock_order: Any,
    ) -> None:
        """Test that first + after returns CursorForwardPagination."""
        cursor = encode_cursor("test-cursor-value")
        result = adapter.build_pagination(
            first=10,
            after=cursor,
            forward_cursor_condition_factory=mock_cursor_factory,
            default_order=mock_order,
        )

        assert isinstance(result, CursorForwardPagination)
        assert result.first == 10
        mock_cursor_factory.assert_called_once_with("test-cursor-value")
        assert result.default_order is mock_order

    def test_build_pagination_backward_cursor(
        self,
        adapter: BaseGQLAdapter,
        mock_cursor_factory: MagicMock,
        mock_order: Any,
    ) -> None:
        """Test that last + before returns CursorBackwardPagination."""
        cursor = encode_cursor("test-cursor-value")
        result = adapter.build_pagination(
            last=5,
            before=cursor,
            backward_cursor_condition_factory=mock_cursor_factory,
            default_order=mock_order,
        )

        assert isinstance(result, CursorBackwardPagination)
        assert result.last == 5
        mock_cursor_factory.assert_called_once_with("test-cursor-value")
        assert result.default_order is mock_order

    def test_build_pagination_offset(self, adapter: BaseGQLAdapter) -> None:
        """Test that limit + offset returns OffsetPagination."""
        result = adapter.build_pagination(limit=20, offset=10)

        assert isinstance(result, OffsetPagination)
        assert result.limit == 20
        assert result.offset == 10

    def test_build_pagination_offset_without_offset(self, adapter: BaseGQLAdapter) -> None:
        """Test that limit without offset defaults offset to 0."""
        result = adapter.build_pagination(limit=20)

        assert isinstance(result, OffsetPagination)
        assert result.limit == 20
        assert result.offset == 0

    def test_build_pagination_default(self, adapter: BaseGQLAdapter) -> None:
        """Test that no parameters returns default OffsetPagination."""
        result = adapter.build_pagination()

        assert isinstance(result, OffsetPagination)
        assert result.limit == DEFAULT_PAGINATION_LIMIT
        assert result.offset == 0

    def test_build_pagination_mixed_modes_first_and_limit_error(
        self, adapter: BaseGQLAdapter
    ) -> None:
        """Test that first + limit raises InvalidGraphQLParameters."""
        with pytest.raises(InvalidGraphQLParameters) as exc_info:
            adapter.build_pagination(first=10, limit=20)
        assert "Only one pagination mode allowed" in str(exc_info.value)

    def test_build_pagination_mixed_modes_last_and_limit_error(
        self, adapter: BaseGQLAdapter
    ) -> None:
        """Test that last + limit raises InvalidGraphQLParameters."""
        with pytest.raises(InvalidGraphQLParameters) as exc_info:
            adapter.build_pagination(last=10, limit=20)
        assert "Only one pagination mode allowed" in str(exc_info.value)

    def test_build_pagination_mixed_modes_first_and_last_error(
        self, adapter: BaseGQLAdapter
    ) -> None:
        """Test that first + last raises InvalidGraphQLParameters."""
        with pytest.raises(InvalidGraphQLParameters) as exc_info:
            adapter.build_pagination(first=10, last=10)
        assert "Only one pagination mode allowed" in str(exc_info.value)

    def test_build_pagination_first_without_after_error(self, adapter: BaseGQLAdapter) -> None:
        """Test that first without after raises InvalidGraphQLParameters."""
        with pytest.raises(InvalidGraphQLParameters) as exc_info:
            adapter.build_pagination(first=10)
        assert "after cursor is required" in str(exc_info.value)

    def test_build_pagination_last_without_before_error(self, adapter: BaseGQLAdapter) -> None:
        """Test that last without before raises InvalidGraphQLParameters."""
        with pytest.raises(InvalidGraphQLParameters) as exc_info:
            adapter.build_pagination(last=10)
        assert "before cursor is required" in str(exc_info.value)

    def test_build_pagination_cursor_without_factory_error(
        self, adapter: BaseGQLAdapter, mock_order: Any
    ) -> None:
        """Test that cursor pagination without cursor_condition_factory raises error."""
        cursor = encode_cursor("test-value")
        with pytest.raises(InvalidGraphQLParameters) as exc_info:
            adapter.build_pagination(
                first=10,
                after=cursor,
                default_order=mock_order,
                # forward_cursor_condition_factory is missing
            )
        assert "forward_cursor_condition_factory and default_order are required" in str(
            exc_info.value
        )

    def test_build_pagination_cursor_without_order_error(
        self, adapter: BaseGQLAdapter, mock_cursor_factory: MagicMock
    ) -> None:
        """Test that cursor pagination without default_order raises error."""
        cursor = encode_cursor("test-value")
        with pytest.raises(InvalidGraphQLParameters) as exc_info:
            adapter.build_pagination(
                first=10,
                after=cursor,
                forward_cursor_condition_factory=mock_cursor_factory,
                # default_order is missing
            )
        assert "forward_cursor_condition_factory and default_order are required" in str(
            exc_info.value
        )

    def test_build_pagination_first_must_be_positive(
        self,
        adapter: BaseGQLAdapter,
        mock_cursor_factory: MagicMock,
        mock_order: Any,
    ) -> None:
        """Test that first <= 0 raises InvalidGraphQLParameters."""
        cursor = encode_cursor("test-value")
        with pytest.raises(InvalidGraphQLParameters) as exc_info:
            adapter.build_pagination(
                first=0,
                after=cursor,
                forward_cursor_condition_factory=mock_cursor_factory,
                default_order=mock_order,
            )
        assert "first must be positive" in str(exc_info.value)

    def test_build_pagination_last_must_be_positive(
        self,
        adapter: BaseGQLAdapter,
        mock_cursor_factory: MagicMock,
        mock_order: Any,
    ) -> None:
        """Test that last <= 0 raises InvalidGraphQLParameters."""
        cursor = encode_cursor("test-value")
        with pytest.raises(InvalidGraphQLParameters) as exc_info:
            adapter.build_pagination(
                last=-1,
                before=cursor,
                backward_cursor_condition_factory=mock_cursor_factory,
                default_order=mock_order,
            )
        assert "last must be positive" in str(exc_info.value)

    def test_build_pagination_limit_must_be_positive(self, adapter: BaseGQLAdapter) -> None:
        """Test that limit <= 0 raises InvalidGraphQLParameters."""
        with pytest.raises(InvalidGraphQLParameters) as exc_info:
            adapter.build_pagination(limit=0)
        assert "limit must be positive" in str(exc_info.value)

    def test_build_pagination_offset_must_be_non_negative(self, adapter: BaseGQLAdapter) -> None:
        """Test that negative offset raises InvalidGraphQLParameters."""
        with pytest.raises(InvalidGraphQLParameters) as exc_info:
            adapter.build_pagination(limit=10, offset=-1)
        assert "offset must be non-negative" in str(exc_info.value)
