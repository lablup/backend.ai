"""
Tests for resource group GraphQL adapter classes.
Tests conversion from GraphQL filter objects to repository Querier objects.
"""

from __future__ import annotations

from ai.backend.manager.api.gql.adapter import (
    BaseGQLAdapter,
    PaginationOptions,
    PaginationSpec,
)
from ai.backend.manager.api.gql.base import OrderDirection, StringFilter
from ai.backend.manager.api.gql.resource_group.types import (
    ResourceGroupFilterGQL,
    ResourceGroupOrderByGQL,
    ResourceGroupOrderFieldGQL,
)
from ai.backend.manager.repositories.base import OffsetPagination
from ai.backend.manager.repositories.scaling_group.options import (
    ScalingGroupConditions,
    ScalingGroupOrders,
)


def _get_pagination_spec() -> PaginationSpec:
    """Create pagination spec for resource groups.

    For typical "newest first" lists:
    - Forward (first/after): DESC order, shows newer items first, next page shows older items
    - Backward (last/before): ASC order, fetches older items first (reversed for display)
    """
    return PaginationSpec(
        forward_order=ScalingGroupOrders.created_at(ascending=False),
        backward_order=ScalingGroupOrders.created_at(ascending=True),
        forward_condition_factory=ScalingGroupConditions.by_cursor_forward,
        backward_condition_factory=ScalingGroupConditions.by_cursor_backward,
    )


class TestBaseGQLAdapter:
    """Test cases for BaseGQLAdapter with resource group types"""

    def test_empty_querier(self) -> None:
        """Test building querier with no filters, orders, or pagination returns default pagination"""
        adapter = BaseGQLAdapter()
        querier = adapter.build_querier(
            PaginationOptions(),
            _get_pagination_spec(),
        )

        assert len(querier.conditions) == 0
        # Default order is applied for offset pagination when order_by is not provided
        assert len(querier.orders) == 1
        # Default pagination is applied
        assert querier.pagination is not None
        assert isinstance(querier.pagination, OffsetPagination)

    def test_name_equals_case_sensitive(self) -> None:
        """Test name equals filter (case-sensitive)"""
        filter_obj = ResourceGroupFilterGQL(
            name=StringFilter(equals="default"),
        )
        adapter = BaseGQLAdapter()
        querier = adapter.build_querier(
            PaginationOptions(),
            _get_pagination_spec(),
            filter=filter_obj,
        )

        assert len(querier.conditions) == 1
        # Verify condition is callable and returns ColumnElement
        condition_result = querier.conditions[0]()
        assert condition_result is not None

    def test_name_equals_case_insensitive(self) -> None:
        """Test name equals filter (case-insensitive)"""
        filter_obj = ResourceGroupFilterGQL(
            name=StringFilter(i_equals="default"),
        )
        adapter = BaseGQLAdapter()
        querier = adapter.build_querier(
            PaginationOptions(),
            _get_pagination_spec(),
            filter=filter_obj,
        )

        assert len(querier.conditions) == 1
        condition_result = querier.conditions[0]()
        assert condition_result is not None

    def test_name_contains_case_sensitive(self) -> None:
        """Test name contains filter (case-sensitive)"""
        filter_obj = ResourceGroupFilterGQL(
            name=StringFilter(contains="def"),
        )
        adapter = BaseGQLAdapter()
        querier = adapter.build_querier(
            PaginationOptions(),
            _get_pagination_spec(),
            filter=filter_obj,
        )

        assert len(querier.conditions) == 1
        condition_result = querier.conditions[0]()
        assert condition_result is not None

    def test_name_contains_case_insensitive(self) -> None:
        """Test name contains filter (case-insensitive)"""
        filter_obj = ResourceGroupFilterGQL(
            name=StringFilter(i_contains="def"),
        )
        adapter = BaseGQLAdapter()
        querier = adapter.build_querier(
            PaginationOptions(),
            _get_pagination_spec(),
            filter=filter_obj,
        )

        assert len(querier.conditions) == 1
        condition_result = querier.conditions[0]()
        assert condition_result is not None

    def test_or_logical_operator(self) -> None:
        """Test OR logical operator"""
        filter_obj = ResourceGroupFilterGQL(
            OR=[
                ResourceGroupFilterGQL(name=StringFilter(equals="default")),
                ResourceGroupFilterGQL(name=StringFilter(equals="custom")),
            ],
        )
        adapter = BaseGQLAdapter()
        querier = adapter.build_querier(
            PaginationOptions(),
            _get_pagination_spec(),
            filter=filter_obj,
        )

        # Should have 1 combined OR condition
        assert len(querier.conditions) == 1
        condition_result = querier.conditions[0]()
        assert condition_result is not None

        # Should have 1 negated condition
        assert len(querier.conditions) == 1
        condition_result = querier.conditions[0]()
        assert condition_result is not None

    def test_order_by_name_ascending(self) -> None:
        """Test ordering by name ascending"""
        order_by = [
            ResourceGroupOrderByGQL(
                field=ResourceGroupOrderFieldGQL.NAME,
                direction=OrderDirection.ASC,
            )
        ]
        adapter = BaseGQLAdapter()
        querier = adapter.build_querier(
            PaginationOptions(limit=10),
            _get_pagination_spec(),
            order_by=order_by,
        )

        assert len(querier.orders) == 1
        assert querier.orders[0] is not None

    def test_order_by_name_descending(self) -> None:
        """Test ordering by name descending"""
        order_by = [
            ResourceGroupOrderByGQL(
                field=ResourceGroupOrderFieldGQL.NAME,
                direction=OrderDirection.DESC,
            )
        ]
        adapter = BaseGQLAdapter()
        querier = adapter.build_querier(
            PaginationOptions(limit=10),
            _get_pagination_spec(),
            order_by=order_by,
        )

        assert len(querier.orders) == 1
        assert querier.orders[0] is not None

    def test_pagination_limit_offset(self) -> None:
        """Test pagination with limit and offset"""
        adapter = BaseGQLAdapter()
        querier = adapter.build_querier(
            PaginationOptions(limit=10, offset=5),
            _get_pagination_spec(),
        )

        assert querier.pagination is not None
        assert isinstance(querier.pagination, OffsetPagination)
        assert querier.pagination.limit == 10
        assert querier.pagination.offset == 5
