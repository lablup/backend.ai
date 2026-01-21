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

    def test_description_equals_case_sensitive(self) -> None:
        """Test description equals filter (case-sensitive)"""
        filter_obj = ResourceGroupFilterGQL(
            description=StringFilter(equals="Test Description"),
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

    def test_description_equals_case_insensitive(self) -> None:
        """Test description equals filter (case-insensitive)"""
        filter_obj = ResourceGroupFilterGQL(
            description=StringFilter(i_equals="test description"),
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

    def test_description_contains_case_sensitive(self) -> None:
        """Test description contains filter (case-sensitive)"""
        filter_obj = ResourceGroupFilterGQL(
            description=StringFilter(contains="Test"),
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

    def test_description_contains_case_insensitive(self) -> None:
        """Test description contains filter (case-insensitive)"""
        filter_obj = ResourceGroupFilterGQL(
            description=StringFilter(i_contains="test"),
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

    def test_is_active_filter_true(self) -> None:
        """Test is_active filter (True)"""
        filter_obj = ResourceGroupFilterGQL(is_active=True)
        adapter = BaseGQLAdapter()
        querier = adapter.build_querier(
            PaginationOptions(),
            _get_pagination_spec(),
            filter=filter_obj,
        )

        assert len(querier.conditions) == 1
        condition_result = querier.conditions[0]()
        assert condition_result is not None

    def test_is_active_filter_false(self) -> None:
        """Test is_active filter (False)"""
        filter_obj = ResourceGroupFilterGQL(is_active=False)
        adapter = BaseGQLAdapter()
        querier = adapter.build_querier(
            PaginationOptions(),
            _get_pagination_spec(),
            filter=filter_obj,
        )

        assert len(querier.conditions) == 1
        condition_result = querier.conditions[0]()
        assert condition_result is not None

    def test_is_public_filter_true(self) -> None:
        """Test is_public filter (True)"""
        filter_obj = ResourceGroupFilterGQL(is_public=True)
        adapter = BaseGQLAdapter()
        querier = adapter.build_querier(
            PaginationOptions(),
            _get_pagination_spec(),
            filter=filter_obj,
        )

        assert len(querier.conditions) == 1
        condition_result = querier.conditions[0]()
        assert condition_result is not None

    def test_is_public_filter_false(self) -> None:
        """Test is_public filter (False)"""
        filter_obj = ResourceGroupFilterGQL(is_public=False)
        adapter = BaseGQLAdapter()
        querier = adapter.build_querier(
            PaginationOptions(),
            _get_pagination_spec(),
            filter=filter_obj,
        )

        assert len(querier.conditions) == 1
        condition_result = querier.conditions[0]()
        assert condition_result is not None

    def test_scheduler_filter(self) -> None:
        """Test scheduler filter"""
        filter_obj = ResourceGroupFilterGQL(scheduler="fifo")
        adapter = BaseGQLAdapter()
        querier = adapter.build_querier(
            PaginationOptions(),
            _get_pagination_spec(),
            filter=filter_obj,
        )

        assert len(querier.conditions) == 1
        condition_result = querier.conditions[0]()
        assert condition_result is not None

    def test_use_host_network_filter_true(self) -> None:
        """Test use_host_network filter (True)"""
        filter_obj = ResourceGroupFilterGQL(use_host_network=True)
        adapter = BaseGQLAdapter()
        querier = adapter.build_querier(
            PaginationOptions(),
            _get_pagination_spec(),
            filter=filter_obj,
        )

        assert len(querier.conditions) == 1
        condition_result = querier.conditions[0]()
        assert condition_result is not None

    def test_use_host_network_filter_false(self) -> None:
        """Test use_host_network filter (False)"""
        filter_obj = ResourceGroupFilterGQL(use_host_network=False)
        adapter = BaseGQLAdapter()
        querier = adapter.build_querier(
            PaginationOptions(),
            _get_pagination_spec(),
            filter=filter_obj,
        )

        assert len(querier.conditions) == 1
        condition_result = querier.conditions[0]()
        assert condition_result is not None

    def test_multiple_filters_combined(self) -> None:
        """Test multiple filters combined"""
        filter_obj = ResourceGroupFilterGQL(
            name=StringFilter(contains="default"),
            is_active=True,
            is_public=True,
        )
        adapter = BaseGQLAdapter()
        querier = adapter.build_querier(
            PaginationOptions(),
            _get_pagination_spec(),
            filter=filter_obj,
        )

        # Should have 3 conditions
        assert len(querier.conditions) == 3
        for condition in querier.conditions:
            assert condition() is not None

    def test_and_logical_operator(self) -> None:
        """Test AND logical operator"""
        filter_obj = ResourceGroupFilterGQL(
            name=StringFilter(contains="default"),
            AND=[
                ResourceGroupFilterGQL(is_active=True),
                ResourceGroupFilterGQL(scheduler="fifo"),
            ],
        )
        adapter = BaseGQLAdapter()
        querier = adapter.build_querier(
            PaginationOptions(),
            _get_pagination_spec(),
            filter=filter_obj,
        )

        # Should have 3 conditions (name + 2 AND conditions)
        assert len(querier.conditions) == 3
        for condition in querier.conditions:
            assert condition() is not None

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

    def test_not_logical_operator(self) -> None:
        """Test NOT logical operator"""
        filter_obj = ResourceGroupFilterGQL(
            NOT=[
                ResourceGroupFilterGQL(is_active=False),
            ],
        )
        adapter = BaseGQLAdapter()
        querier = adapter.build_querier(
            PaginationOptions(),
            _get_pagination_spec(),
            filter=filter_obj,
        )

        # Should have 1 negated condition
        assert len(querier.conditions) == 1
        condition_result = querier.conditions[0]()
        assert condition_result is not None

    def test_complex_logical_operators(self) -> None:
        """Test complex combination of AND, OR, NOT operators"""
        filter_obj = ResourceGroupFilterGQL(
            name=StringFilter(contains="default"),
            AND=[
                ResourceGroupFilterGQL(is_active=True),
            ],
            OR=[
                ResourceGroupFilterGQL(scheduler="fifo"),
                ResourceGroupFilterGQL(use_host_network=True),
            ],
            NOT=[
                ResourceGroupFilterGQL(is_public=False),
            ],
        )
        adapter = BaseGQLAdapter()
        querier = adapter.build_querier(
            PaginationOptions(),
            _get_pagination_spec(),
            filter=filter_obj,
        )

        # Should have 4 conditions: name + AND + OR (combined) + NOT (negated)
        assert len(querier.conditions) == 4
        for condition in querier.conditions:
            assert condition() is not None

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

    def test_order_by_created_at_ascending(self) -> None:
        """Test ordering by created_at ascending"""
        order_by = [
            ResourceGroupOrderByGQL(
                field=ResourceGroupOrderFieldGQL.CREATED_AT,
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

    def test_order_by_created_at_descending(self) -> None:
        """Test ordering by created_at descending"""
        order_by = [
            ResourceGroupOrderByGQL(
                field=ResourceGroupOrderFieldGQL.CREATED_AT,
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

    def test_order_by_is_active_ascending(self) -> None:
        """Test ordering by is_active ascending"""
        order_by = [
            ResourceGroupOrderByGQL(
                field=ResourceGroupOrderFieldGQL.IS_ACTIVE,
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

    def test_order_by_is_active_descending(self) -> None:
        """Test ordering by is_active descending"""
        order_by = [
            ResourceGroupOrderByGQL(
                field=ResourceGroupOrderFieldGQL.IS_ACTIVE,
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

    def test_order_by_is_public_ascending(self) -> None:
        """Test ordering by is_public ascending"""
        order_by = [
            ResourceGroupOrderByGQL(
                field=ResourceGroupOrderFieldGQL.IS_PUBLIC,
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

    def test_order_by_is_public_descending(self) -> None:
        """Test ordering by is_public descending"""
        order_by = [
            ResourceGroupOrderByGQL(
                field=ResourceGroupOrderFieldGQL.IS_PUBLIC,
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

    def test_multiple_order_by(self) -> None:
        """Test multiple order by fields"""
        order_by = [
            ResourceGroupOrderByGQL(
                field=ResourceGroupOrderFieldGQL.IS_ACTIVE,
                direction=OrderDirection.DESC,
            ),
            ResourceGroupOrderByGQL(
                field=ResourceGroupOrderFieldGQL.NAME,
                direction=OrderDirection.ASC,
            ),
        ]
        adapter = BaseGQLAdapter()
        querier = adapter.build_querier(
            PaginationOptions(limit=10),
            _get_pagination_spec(),
            order_by=order_by,
        )

        assert len(querier.orders) == 2
        assert querier.orders[0] is not None
        assert querier.orders[1] is not None

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

    def test_filter_order_pagination_combined(self) -> None:
        """Test filter, order, and pagination all combined"""
        filter_obj = ResourceGroupFilterGQL(
            name=StringFilter(contains="default"),
            is_active=True,
        )
        order_by = [
            ResourceGroupOrderByGQL(
                field=ResourceGroupOrderFieldGQL.NAME,
                direction=OrderDirection.ASC,
            )
        ]
        adapter = BaseGQLAdapter()
        querier = adapter.build_querier(
            PaginationOptions(limit=20, offset=10),
            _get_pagination_spec(),
            filter=filter_obj,
            order_by=order_by,
        )

        assert len(querier.conditions) == 2
        assert len(querier.orders) == 1
        assert querier.pagination is not None
        assert isinstance(querier.pagination, OffsetPagination)
        assert querier.pagination.limit == 20
        assert querier.pagination.offset == 10
