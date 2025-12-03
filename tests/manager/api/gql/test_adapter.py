"""Tests for GraphQL adapter utilities including pagination building."""

from __future__ import annotations

from typing import Any
from unittest.mock import MagicMock

import pytest

from ai.backend.manager.api.gql.adapter import (
    DEFAULT_PAGINATION_LIMIT,
    BaseGQLAdapter,
    CursorPaginationFactories,
    PaginationOptions,
)
from ai.backend.manager.api.gql.base import encode_cursor
from ai.backend.manager.errors.api import InvalidGraphQLParameters
from ai.backend.manager.repositories.base import (
    CursorBackwardPagination,
    CursorForwardPagination,
    OffsetPagination,
)


class TestBaseGQLAdapterBuildPagination:
    """Tests for BaseGQLAdapter._build_pagination method via build_querier."""

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

    @pytest.fixture
    def cursor_factories(
        self, mock_cursor_factory: MagicMock, mock_order: Any
    ) -> CursorPaginationFactories:
        """Create CursorPaginationFactories with mocks."""
        return CursorPaginationFactories(
            cursor_order=mock_order,
            forward_cursor_condition_factory=mock_cursor_factory,
            backward_cursor_condition_factory=mock_cursor_factory,
        )

    def test_build_pagination_forward_cursor(
        self,
        adapter: BaseGQLAdapter,
        mock_cursor_factory: MagicMock,
        mock_order: Any,
        cursor_factories: CursorPaginationFactories,
    ) -> None:
        """Test that first + after returns CursorForwardPagination."""
        cursor = encode_cursor("test-cursor-value")
        querier = adapter.build_querier(
            PaginationOptions(first=10, after=cursor),
            cursor_factories,
        )

        assert isinstance(querier.pagination, CursorForwardPagination)
        assert querier.pagination.first == 10
        mock_cursor_factory.assert_called_once_with("test-cursor-value")
        assert querier.pagination.cursor_order is mock_order

    def test_build_pagination_backward_cursor(
        self,
        adapter: BaseGQLAdapter,
        mock_cursor_factory: MagicMock,
        mock_order: Any,
        cursor_factories: CursorPaginationFactories,
    ) -> None:
        """Test that last + before returns CursorBackwardPagination."""
        cursor = encode_cursor("test-cursor-value")
        # Need a fresh factory for backward since we check call count
        backward_factory = MagicMock()
        backward_factory.return_value = MagicMock()
        factories = CursorPaginationFactories(
            cursor_order=mock_order,
            forward_cursor_condition_factory=mock_cursor_factory,
            backward_cursor_condition_factory=backward_factory,
        )
        querier = adapter.build_querier(
            PaginationOptions(last=5, before=cursor),
            factories,
        )

        assert isinstance(querier.pagination, CursorBackwardPagination)
        assert querier.pagination.last == 5
        backward_factory.assert_called_once_with("test-cursor-value")
        assert querier.pagination.cursor_order is mock_order

    def test_build_pagination_offset(
        self, adapter: BaseGQLAdapter, cursor_factories: CursorPaginationFactories
    ) -> None:
        """Test that limit + offset returns OffsetPagination."""
        querier = adapter.build_querier(
            PaginationOptions(limit=20, offset=10),
            cursor_factories,
        )

        assert isinstance(querier.pagination, OffsetPagination)
        assert querier.pagination.limit == 20
        assert querier.pagination.offset == 10

    def test_build_pagination_offset_without_offset(
        self, adapter: BaseGQLAdapter, cursor_factories: CursorPaginationFactories
    ) -> None:
        """Test that limit without offset defaults offset to 0."""
        querier = adapter.build_querier(
            PaginationOptions(limit=20),
            cursor_factories,
        )

        assert isinstance(querier.pagination, OffsetPagination)
        assert querier.pagination.limit == 20
        assert querier.pagination.offset == 0

    def test_build_pagination_default(
        self, adapter: BaseGQLAdapter, cursor_factories: CursorPaginationFactories
    ) -> None:
        """Test that no parameters returns default OffsetPagination."""
        querier = adapter.build_querier(
            PaginationOptions(),
            cursor_factories,
        )

        assert isinstance(querier.pagination, OffsetPagination)
        assert querier.pagination.limit == DEFAULT_PAGINATION_LIMIT
        assert querier.pagination.offset == 0

    def test_build_pagination_mixed_modes_first_and_limit_error(
        self, adapter: BaseGQLAdapter, cursor_factories: CursorPaginationFactories
    ) -> None:
        """Test that first + limit raises InvalidGraphQLParameters."""
        with pytest.raises(InvalidGraphQLParameters) as exc_info:
            adapter.build_querier(
                PaginationOptions(first=10, limit=20),
                cursor_factories,
            )
        assert "Only one pagination mode allowed" in str(exc_info.value)

    def test_build_pagination_mixed_modes_last_and_limit_error(
        self, adapter: BaseGQLAdapter, cursor_factories: CursorPaginationFactories
    ) -> None:
        """Test that last + limit raises InvalidGraphQLParameters."""
        with pytest.raises(InvalidGraphQLParameters) as exc_info:
            adapter.build_querier(
                PaginationOptions(last=10, limit=20),
                cursor_factories,
            )
        assert "Only one pagination mode allowed" in str(exc_info.value)

    def test_build_pagination_mixed_modes_first_and_last_error(
        self, adapter: BaseGQLAdapter, cursor_factories: CursorPaginationFactories
    ) -> None:
        """Test that first + last raises InvalidGraphQLParameters."""
        with pytest.raises(InvalidGraphQLParameters) as exc_info:
            adapter.build_querier(
                PaginationOptions(first=10, last=10),
                cursor_factories,
            )
        assert "Only one pagination mode allowed" in str(exc_info.value)

    def test_build_pagination_first_without_after(
        self,
        adapter: BaseGQLAdapter,
        mock_order: Any,
        cursor_factories: CursorPaginationFactories,
    ) -> None:
        """Test that first without after returns CursorForwardPagination with no cursor condition."""
        querier = adapter.build_querier(
            PaginationOptions(first=10),
            cursor_factories,
        )

        assert isinstance(querier.pagination, CursorForwardPagination)
        assert querier.pagination.first == 10
        assert querier.pagination.cursor_condition is None
        assert querier.pagination.cursor_order is mock_order

    def test_build_pagination_last_without_before(
        self,
        adapter: BaseGQLAdapter,
        mock_order: Any,
        cursor_factories: CursorPaginationFactories,
    ) -> None:
        """Test that last without before returns CursorBackwardPagination with no cursor condition."""
        querier = adapter.build_querier(
            PaginationOptions(last=10),
            cursor_factories,
        )

        assert isinstance(querier.pagination, CursorBackwardPagination)
        assert querier.pagination.last == 10
        assert querier.pagination.cursor_condition is None
        assert querier.pagination.cursor_order is mock_order

    def test_build_pagination_first_must_be_positive(
        self,
        adapter: BaseGQLAdapter,
        cursor_factories: CursorPaginationFactories,
    ) -> None:
        """Test that first <= 0 raises InvalidGraphQLParameters."""
        with pytest.raises(InvalidGraphQLParameters) as exc_info:
            adapter.build_querier(
                PaginationOptions(first=0),
                cursor_factories,
            )
        assert "first must be positive" in str(exc_info.value)

    def test_build_pagination_last_must_be_positive(
        self,
        adapter: BaseGQLAdapter,
        cursor_factories: CursorPaginationFactories,
    ) -> None:
        """Test that last <= 0 raises InvalidGraphQLParameters."""
        with pytest.raises(InvalidGraphQLParameters) as exc_info:
            adapter.build_querier(
                PaginationOptions(last=-1),
                cursor_factories,
            )
        assert "last must be positive" in str(exc_info.value)

    def test_build_pagination_limit_must_be_positive(
        self, adapter: BaseGQLAdapter, cursor_factories: CursorPaginationFactories
    ) -> None:
        """Test that limit <= 0 raises InvalidGraphQLParameters."""
        with pytest.raises(InvalidGraphQLParameters) as exc_info:
            adapter.build_querier(
                PaginationOptions(limit=0),
                cursor_factories,
            )
        assert "limit must be positive" in str(exc_info.value)

    def test_build_pagination_offset_must_be_non_negative(
        self, adapter: BaseGQLAdapter, cursor_factories: CursorPaginationFactories
    ) -> None:
        """Test that negative offset raises InvalidGraphQLParameters."""
        with pytest.raises(InvalidGraphQLParameters) as exc_info:
            adapter.build_querier(
                PaginationOptions(limit=10, offset=-1),
                cursor_factories,
            )
        assert "offset must be non-negative" in str(exc_info.value)
