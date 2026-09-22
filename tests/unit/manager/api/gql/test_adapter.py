"""Tests for GraphQL adapter utilities including pagination building."""

from __future__ import annotations

import uuid
from http import HTTPStatus
from typing import Any
from unittest.mock import MagicMock

import pytest
import sqlalchemy as sa
from sqlalchemy.orm import DeclarativeBase, Mapped, mapped_column

from ai.backend.common.exception import BackendAIError
from ai.backend.manager.api.adapter_options.pagination.pagination import DEFAULT_PAGINATION_LIMIT
from ai.backend.manager.api.gql.adapter import (
    BaseGQLAdapter,
    PaginationOptions,
    PaginationSpec,
)
from ai.backend.manager.api.gql.base import encode_cursor
from ai.backend.manager.errors.api import InvalidCursor, InvalidGraphQLParameters
from ai.backend.manager.repositories.base import (
    CursorBackwardPagination,
    CursorForwardPagination,
    OffsetPagination,
)


class _Base(DeclarativeBase):
    pass


class _ItemRow(_Base):
    __tablename__ = "items"

    id: Mapped[uuid.UUID] = mapped_column("id", sa.Uuid, primary_key=True)
    created_at: Mapped[int] = mapped_column("created_at", sa.Integer)


class TestBaseGQLAdapterBuildPagination:
    """Tests for BaseGQLAdapter._build_pagination method via build_querier."""

    @pytest.fixture
    def adapter(self) -> BaseGQLAdapter:
        """Create a BaseGQLAdapter instance."""
        return BaseGQLAdapter()

    @pytest.fixture
    def mock_forward_order(self) -> Any:
        """Create a forward cursor order."""
        return _ItemRow.created_at.desc()

    @pytest.fixture
    def pagination_spec(
        self,
        mock_forward_order: Any,
    ) -> PaginationSpec:
        """Create PaginationSpec over the test table."""
        return PaginationSpec(
            forward_order=mock_forward_order,
            cursor_column=_ItemRow.id,
        )

    def test_build_pagination_forward_cursor(
        self,
        adapter: BaseGQLAdapter,
        mock_forward_order: Any,
        pagination_spec: PaginationSpec,
    ) -> None:
        """Test that first + after returns CursorForwardPagination."""
        cursor = encode_cursor(uuid.uuid4())
        querier = adapter.build_querier(
            PaginationOptions(first=10, after=cursor),
            pagination_spec,
        )

        assert isinstance(querier.pagination, CursorForwardPagination)
        assert querier.pagination.first == 10
        assert querier.pagination.cursor_condition is not None
        assert querier.pagination.cursor_order is mock_forward_order

    def test_build_pagination_backward_cursor(
        self,
        adapter: BaseGQLAdapter,
        pagination_spec: PaginationSpec,
    ) -> None:
        """Test that last + before returns CursorBackwardPagination."""
        cursor = encode_cursor(uuid.uuid4())
        querier = adapter.build_querier(
            PaginationOptions(last=5, before=cursor),
            pagination_spec,
        )

        assert isinstance(querier.pagination, CursorBackwardPagination)
        assert querier.pagination.last == 5
        assert querier.pagination.cursor_condition is not None
        assert querier.pagination.cursor_order.compare(_ItemRow.created_at.asc())
        assert querier.orders[-1].compare(_ItemRow.id.desc())

    def test_build_pagination_offset(
        self, adapter: BaseGQLAdapter, pagination_spec: PaginationSpec
    ) -> None:
        """Test that limit + offset returns OffsetPagination."""
        querier = adapter.build_querier(
            PaginationOptions(limit=20, offset=10),
            pagination_spec,
        )

        assert isinstance(querier.pagination, OffsetPagination)
        assert querier.pagination.limit == 20
        assert querier.pagination.offset == 10

    def test_build_pagination_offset_without_offset(
        self, adapter: BaseGQLAdapter, pagination_spec: PaginationSpec
    ) -> None:
        """Test that limit without offset defaults offset to 0."""
        querier = adapter.build_querier(
            PaginationOptions(limit=20),
            pagination_spec,
        )

        assert isinstance(querier.pagination, OffsetPagination)
        assert querier.pagination.limit == 20
        assert querier.pagination.offset == 0

    def test_build_pagination_default(
        self, adapter: BaseGQLAdapter, pagination_spec: PaginationSpec
    ) -> None:
        """Test that no parameters returns default OffsetPagination."""
        querier = adapter.build_querier(
            PaginationOptions(),
            pagination_spec,
        )

        assert isinstance(querier.pagination, OffsetPagination)
        assert querier.pagination.limit == DEFAULT_PAGINATION_LIMIT
        assert querier.pagination.offset == 0

    def test_build_pagination_mixed_modes_first_and_limit_error(
        self, adapter: BaseGQLAdapter, pagination_spec: PaginationSpec
    ) -> None:
        """Test that first + limit raises InvalidGraphQLParameters."""
        with pytest.raises(InvalidGraphQLParameters) as exc_info:
            adapter.build_querier(
                PaginationOptions(first=10, limit=20),
                pagination_spec,
            )
        assert "Only one pagination mode allowed" in str(exc_info.value)

    def test_build_pagination_mixed_modes_last_and_limit_error(
        self, adapter: BaseGQLAdapter, pagination_spec: PaginationSpec
    ) -> None:
        """Test that last + limit raises InvalidGraphQLParameters."""
        with pytest.raises(InvalidGraphQLParameters) as exc_info:
            adapter.build_querier(
                PaginationOptions(last=10, limit=20),
                pagination_spec,
            )
        assert "Only one pagination mode allowed" in str(exc_info.value)

    def test_build_pagination_mixed_modes_first_and_last_error(
        self, adapter: BaseGQLAdapter, pagination_spec: PaginationSpec
    ) -> None:
        """Test that first + last raises InvalidGraphQLParameters."""
        with pytest.raises(InvalidGraphQLParameters) as exc_info:
            adapter.build_querier(
                PaginationOptions(first=10, last=10),
                pagination_spec,
            )
        assert "Only one pagination mode allowed" in str(exc_info.value)

    def test_build_pagination_mixed_modes_first_and_offset_error(
        self, adapter: BaseGQLAdapter, pagination_spec: PaginationSpec
    ) -> None:
        """Test that first + offset raises InvalidGraphQLParameters."""
        with pytest.raises(InvalidGraphQLParameters) as exc_info:
            adapter.build_querier(
                PaginationOptions(first=10, offset=0),
                pagination_spec,
            )
        assert "Only one pagination mode allowed" in str(exc_info.value)

    def test_build_pagination_mixed_modes_last_and_offset_error(
        self, adapter: BaseGQLAdapter, pagination_spec: PaginationSpec
    ) -> None:
        """Test that last + offset raises InvalidGraphQLParameters."""
        with pytest.raises(InvalidGraphQLParameters) as exc_info:
            adapter.build_querier(
                PaginationOptions(last=5, offset=0),
                pagination_spec,
            )
        assert "Only one pagination mode allowed" in str(exc_info.value)

    def test_build_pagination_mixed_modes_after_and_limit_error(
        self, adapter: BaseGQLAdapter, pagination_spec: PaginationSpec
    ) -> None:
        """Test that after + limit raises InvalidGraphQLParameters."""
        with pytest.raises(InvalidGraphQLParameters) as exc_info:
            adapter.build_querier(
                PaginationOptions(after="cursor", limit=10),
                pagination_spec,
            )
        assert "Only one pagination mode allowed" in str(exc_info.value)

    def test_build_pagination_mixed_modes_before_and_limit_error(
        self, adapter: BaseGQLAdapter, pagination_spec: PaginationSpec
    ) -> None:
        """Test that before + limit raises InvalidGraphQLParameters."""
        with pytest.raises(InvalidGraphQLParameters) as exc_info:
            adapter.build_querier(
                PaginationOptions(before="cursor", limit=10),
                pagination_spec,
            )
        assert "Only one pagination mode allowed" in str(exc_info.value)

    def test_build_pagination_mixed_modes_first_and_before_error(
        self, adapter: BaseGQLAdapter, pagination_spec: PaginationSpec
    ) -> None:
        """Test that first + before raises InvalidGraphQLParameters (forward + backward)."""
        with pytest.raises(InvalidGraphQLParameters) as exc_info:
            adapter.build_querier(
                PaginationOptions(first=10, before="cursor"),
                pagination_spec,
            )
        assert "Only one pagination mode allowed" in str(exc_info.value)

    def test_build_pagination_mixed_modes_after_and_last_error(
        self, adapter: BaseGQLAdapter, pagination_spec: PaginationSpec
    ) -> None:
        """Test that after + last raises InvalidGraphQLParameters (forward + backward)."""
        with pytest.raises(InvalidGraphQLParameters) as exc_info:
            adapter.build_querier(
                PaginationOptions(after="cursor", last=5),
                pagination_spec,
            )
        assert "Only one pagination mode allowed" in str(exc_info.value)

    def test_build_pagination_first_without_after(
        self,
        adapter: BaseGQLAdapter,
        mock_forward_order: Any,
        pagination_spec: PaginationSpec,
    ) -> None:
        """Test that first without after returns CursorForwardPagination with no cursor condition."""
        querier = adapter.build_querier(
            PaginationOptions(first=10),
            pagination_spec,
        )

        assert isinstance(querier.pagination, CursorForwardPagination)
        assert querier.pagination.first == 10
        assert querier.pagination.cursor_condition is None
        assert querier.pagination.cursor_order is mock_forward_order

    def test_build_pagination_last_without_before(
        self,
        adapter: BaseGQLAdapter,
        pagination_spec: PaginationSpec,
    ) -> None:
        """Test that last without before returns CursorBackwardPagination with no cursor condition."""
        querier = adapter.build_querier(
            PaginationOptions(last=10),
            pagination_spec,
        )

        assert isinstance(querier.pagination, CursorBackwardPagination)
        assert querier.pagination.last == 10
        assert querier.pagination.cursor_condition is None
        assert querier.pagination.cursor_order.compare(_ItemRow.created_at.asc())

    def test_build_pagination_first_must_be_positive(
        self,
        adapter: BaseGQLAdapter,
        pagination_spec: PaginationSpec,
    ) -> None:
        """Test that first <= 0 raises InvalidGraphQLParameters."""
        with pytest.raises(InvalidGraphQLParameters) as exc_info:
            adapter.build_querier(
                PaginationOptions(first=0),
                pagination_spec,
            )
        assert "first must be positive" in str(exc_info.value)

    def test_build_pagination_last_must_be_positive(
        self,
        adapter: BaseGQLAdapter,
        pagination_spec: PaginationSpec,
    ) -> None:
        """Test that last <= 0 raises InvalidGraphQLParameters."""
        with pytest.raises(InvalidGraphQLParameters) as exc_info:
            adapter.build_querier(
                PaginationOptions(last=-1),
                pagination_spec,
            )
        assert "last must be positive" in str(exc_info.value)

    def test_build_pagination_limit_must_be_positive(
        self, adapter: BaseGQLAdapter, pagination_spec: PaginationSpec
    ) -> None:
        """Test that limit <= 0 raises InvalidGraphQLParameters."""
        with pytest.raises(InvalidGraphQLParameters) as exc_info:
            adapter.build_querier(
                PaginationOptions(limit=0),
                pagination_spec,
            )
        assert "limit must be positive" in str(exc_info.value)

    def test_build_pagination_offset_must_be_non_negative(
        self, adapter: BaseGQLAdapter, pagination_spec: PaginationSpec
    ) -> None:
        """Test that negative offset raises InvalidGraphQLParameters."""
        with pytest.raises(InvalidGraphQLParameters) as exc_info:
            adapter.build_querier(
                PaginationOptions(limit=10, offset=-1),
                pagination_spec,
            )
        assert "offset must be non-negative" in str(exc_info.value)

    def test_offset_pagination_applies_default_order_when_order_by_is_none(
        self,
        adapter: BaseGQLAdapter,
        mock_forward_order: Any,
        pagination_spec: PaginationSpec,
    ) -> None:
        """Test that offset pagination uses forward_order as default when order_by is not provided."""
        querier = adapter.build_querier(
            PaginationOptions(limit=10),
            pagination_spec,
        )

        assert isinstance(querier.pagination, OffsetPagination)
        assert len(querier.orders) == 2
        assert querier.orders[0] is mock_forward_order
        assert querier.orders[-1].compare(_ItemRow.id.asc())

    def test_default_pagination_applies_default_order_when_order_by_is_none(
        self,
        adapter: BaseGQLAdapter,
        mock_forward_order: Any,
        pagination_spec: PaginationSpec,
    ) -> None:
        """Test that default pagination (no params) uses forward_order as default."""
        querier = adapter.build_querier(
            PaginationOptions(),
            pagination_spec,
        )

        assert isinstance(querier.pagination, OffsetPagination)
        assert len(querier.orders) == 2
        assert querier.orders[0] is mock_forward_order
        assert querier.orders[-1].compare(_ItemRow.id.asc())

    def test_offset_pagination_does_not_apply_default_order_when_order_by_is_provided(
        self,
        adapter: BaseGQLAdapter,
        mock_forward_order: Any,
        pagination_spec: PaginationSpec,
    ) -> None:
        """Test that offset pagination does not add default order when order_by is provided."""
        mock_order_by = MagicMock()
        mock_query_order = MagicMock()
        mock_order_by.to_query_order.return_value = mock_query_order

        querier = adapter.build_querier(
            PaginationOptions(limit=10),
            pagination_spec,
            order_by=[mock_order_by],
        )

        assert isinstance(querier.pagination, OffsetPagination)
        assert len(querier.orders) == 2
        assert querier.orders[0] is mock_query_order
        assert querier.orders[0] is not mock_forward_order
        assert querier.orders[-1].compare(_ItemRow.id.asc())

    def test_cursor_pagination_does_not_add_default_order_to_querier_orders(
        self,
        adapter: BaseGQLAdapter,
        pagination_spec: PaginationSpec,
    ) -> None:
        """Test that cursor pagination does not add forward_order to querier.orders."""
        querier = adapter.build_querier(
            PaginationOptions(first=10),
            pagination_spec,
        )

        assert isinstance(querier.pagination, CursorForwardPagination)
        # Cursor pagination should NOT add default order to querier.orders
        # (it uses cursor_order internally in pagination object)
        # But tiebreaker is always appended
        assert len(querier.orders) == 1
        assert querier.orders[0].compare(_ItemRow.id.asc())

    def test_cursor_pagination_drops_order_by(
        self,
        adapter: BaseGQLAdapter,
        pagination_spec: PaginationSpec,
    ) -> None:
        """Cursor pagination sorts by the spec alone, so order_by is dropped."""
        mock_order_by = MagicMock()
        mock_query_order = MagicMock()
        mock_order_by.to_query_order.return_value = mock_query_order

        querier = adapter.build_querier(
            PaginationOptions(first=10),
            pagination_spec,
            order_by=[mock_order_by],
        )

        assert isinstance(querier.pagination, CursorForwardPagination)
        assert mock_query_order not in querier.orders
        assert len(querier.orders) == 1
        assert querier.orders[0].compare(_ItemRow.id.asc())

    def test_cursor_payload_the_entity_cannot_key_on_is_invalid_cursor(
        self,
        adapter: BaseGQLAdapter,
    ) -> None:
        """A payload the spec's cursor parser rejects is the caller's error."""
        uuid_keyed_spec = PaginationSpec(
            forward_order=_ItemRow.created_at.desc(),
            cursor_column=_ItemRow.id,
        )
        cursor = encode_cursor("not-a-uuid")

        with pytest.raises(InvalidCursor) as forward:
            adapter.build_querier(PaginationOptions(first=10, after=cursor), uuid_keyed_spec)
        with pytest.raises(InvalidCursor) as backward:
            adapter.build_querier(PaginationOptions(last=10, before=cursor), uuid_keyed_spec)

        # A BackendAIError carrying a 4xx: the handler reports its code instead of logging a fault.
        for raised in (forward.value, backward.value):
            assert isinstance(raised, BackendAIError)
            assert raised.status_code == HTTPStatus.BAD_REQUEST
