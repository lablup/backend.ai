"""Tests for GraphQL adapter utilities including pagination building."""

from __future__ import annotations

import uuid
from http import HTTPStatus
from unittest.mock import MagicMock

import pytest

from ai.backend.common.exception import BackendAIError
from ai.backend.manager.api.adapter_options.pagination.pagination import DEFAULT_PAGINATION_LIMIT
from ai.backend.manager.api.gql.adapter import (
    BaseGQLAdapter,
    PaginationOptions,
    PaginationSpec,
)
from ai.backend.manager.api.gql.base import encode_cursor
from ai.backend.manager.errors.api import InvalidCursor, InvalidGraphQLParameters
from ai.backend.manager.models.app_config_definition.row import AppConfigDefinitionRow
from ai.backend.manager.models.specs.pagination import (
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
    def pagination_spec(self) -> PaginationSpec:
        return PaginationSpec(
            forward_order=AppConfigDefinitionRow.created_at.desc(),
            tiebreaker_order=AppConfigDefinitionRow.id.asc(),
        )

    def test_build_pagination_forward_cursor(
        self,
        adapter: BaseGQLAdapter,
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
        assert querier.pagination.cursor_order is pagination_spec.forward_order

    def test_build_pagination_backward_cursor(
        self,
        adapter: BaseGQLAdapter,
        pagination_spec: PaginationSpec,
    ) -> None:
        """Test that last + before returns CursorBackwardPagination on the reversed order."""
        cursor = encode_cursor(uuid.uuid4())
        querier = adapter.build_querier(
            PaginationOptions(last=5, before=cursor),
            pagination_spec,
        )

        assert isinstance(querier.pagination, CursorBackwardPagination)
        assert querier.pagination.last == 5
        assert querier.pagination.cursor_condition is not None
        assert str(querier.pagination.cursor_order) == str(AppConfigDefinitionRow.created_at.asc())

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
        assert querier.pagination.cursor_order is pagination_spec.forward_order

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
        assert str(querier.pagination.cursor_order) == str(AppConfigDefinitionRow.created_at.asc())

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
        pagination_spec: PaginationSpec,
    ) -> None:
        """Test that offset pagination uses forward_order as default when order_by is not provided."""
        querier = adapter.build_querier(
            PaginationOptions(limit=10),
            pagination_spec,
        )

        assert isinstance(querier.pagination, OffsetPagination)
        assert len(querier.orders) == 2
        assert querier.orders[0] is pagination_spec.forward_order
        assert querier.orders[-1] is pagination_spec.tiebreaker_order

    def test_default_pagination_applies_default_order_when_order_by_is_none(
        self,
        adapter: BaseGQLAdapter,
        pagination_spec: PaginationSpec,
    ) -> None:
        """Test that default pagination (no params) uses forward_order as default."""
        querier = adapter.build_querier(
            PaginationOptions(),
            pagination_spec,
        )

        assert isinstance(querier.pagination, OffsetPagination)
        assert len(querier.orders) == 2
        assert querier.orders[0] is pagination_spec.forward_order
        assert querier.orders[-1] is pagination_spec.tiebreaker_order

    def test_offset_pagination_does_not_apply_default_order_when_order_by_is_provided(
        self,
        adapter: BaseGQLAdapter,
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
        assert querier.orders[0] is not pagination_spec.forward_order
        assert querier.orders[-1] is pagination_spec.tiebreaker_order

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
        assert querier.orders[0] is pagination_spec.tiebreaker_order

    def test_backward_cursor_pagination_reverses_the_tiebreaker(
        self,
        adapter: BaseGQLAdapter,
        pagination_spec: PaginationSpec,
    ) -> None:
        querier = adapter.build_querier(
            PaginationOptions(last=10),
            pagination_spec,
        )

        assert isinstance(querier.pagination, CursorBackwardPagination)
        assert len(querier.orders) == 1
        assert str(querier.orders[0]) == str(AppConfigDefinitionRow.id.desc())

    def test_cursor_payload_the_entity_cannot_key_on_is_invalid_cursor(
        self,
        adapter: BaseGQLAdapter,
        pagination_spec: PaginationSpec,
    ) -> None:
        """A payload the tiebreaker column cannot hold is the caller's error, not a 500."""
        cursor = encode_cursor("not-a-uuid")

        with pytest.raises(InvalidCursor) as forward:
            adapter.build_querier(PaginationOptions(first=10, after=cursor), pagination_spec)
        with pytest.raises(InvalidCursor) as backward:
            adapter.build_querier(PaginationOptions(last=10, before=cursor), pagination_spec)

        # A BackendAIError carrying a 4xx: the handler reports its code instead of logging a fault.
        for raised in (forward.value, backward.value):
            assert isinstance(raised, BackendAIError)
            assert raised.status_code == HTTPStatus.BAD_REQUEST
