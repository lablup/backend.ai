"""
Tests for scaling group GraphQL adapter classes.
Tests conversion from GraphQL filter objects to repository Querier objects.
"""

from __future__ import annotations

from ai.backend.manager.api.gql.base import OrderDirection, StringFilter
from ai.backend.manager.api.gql.scaling_group.adapter import ScalingGroupGQLAdapter
from ai.backend.manager.api.gql.scaling_group.types import (
    ScalingGroupFilter,
    ScalingGroupOrderBy,
    ScalingGroupOrderField,
)
from ai.backend.manager.repositories.base import OffsetPagination


class TestScalingGroupGQLAdapter:
    """Test cases for ScalingGroupGQLAdapter"""

    def test_empty_querier(self) -> None:
        """Test building querier with no filters, orders, or pagination"""
        adapter = ScalingGroupGQLAdapter()
        querier = adapter.build_querier()

        assert len(querier.conditions) == 0
        assert len(querier.orders) == 0
        assert querier.pagination is None

    def test_name_equals_case_sensitive(self) -> None:
        """Test name equals filter (case-sensitive)"""
        filter_obj = ScalingGroupFilter(
            name=StringFilter(equals="default"),
        )
        adapter = ScalingGroupGQLAdapter()
        querier = adapter.build_querier(filter=filter_obj)

        assert len(querier.conditions) == 1
        # Verify condition is callable and returns ColumnElement
        condition_result = querier.conditions[0]()
        assert condition_result is not None

    def test_name_equals_case_insensitive(self) -> None:
        """Test name equals filter (case-insensitive)"""
        filter_obj = ScalingGroupFilter(
            name=StringFilter(i_equals="default"),
        )
        adapter = ScalingGroupGQLAdapter()
        querier = adapter.build_querier(filter=filter_obj)

        assert len(querier.conditions) == 1
        condition_result = querier.conditions[0]()
        assert condition_result is not None

    def test_name_contains_case_sensitive(self) -> None:
        """Test name contains filter (case-sensitive)"""
        filter_obj = ScalingGroupFilter(
            name=StringFilter(contains="def"),
        )
        adapter = ScalingGroupGQLAdapter()
        querier = adapter.build_querier(filter=filter_obj)

        assert len(querier.conditions) == 1
        condition_result = querier.conditions[0]()
        assert condition_result is not None

    def test_name_contains_case_insensitive(self) -> None:
        """Test name contains filter (case-insensitive)"""
        filter_obj = ScalingGroupFilter(
            name=StringFilter(i_contains="def"),
        )
        adapter = ScalingGroupGQLAdapter()
        querier = adapter.build_querier(filter=filter_obj)

        assert len(querier.conditions) == 1
        condition_result = querier.conditions[0]()
        assert condition_result is not None

    def test_description_equals_case_sensitive(self) -> None:
        """Test description equals filter (case-sensitive)"""
        filter_obj = ScalingGroupFilter(
            description=StringFilter(equals="Test Description"),
        )
        adapter = ScalingGroupGQLAdapter()
        querier = adapter.build_querier(filter=filter_obj)

        assert len(querier.conditions) == 1
        condition_result = querier.conditions[0]()
        assert condition_result is not None

    def test_description_equals_case_insensitive(self) -> None:
        """Test description equals filter (case-insensitive)"""
        filter_obj = ScalingGroupFilter(
            description=StringFilter(i_equals="test description"),
        )
        adapter = ScalingGroupGQLAdapter()
        querier = adapter.build_querier(filter=filter_obj)

        assert len(querier.conditions) == 1
        condition_result = querier.conditions[0]()
        assert condition_result is not None

    def test_description_contains_case_sensitive(self) -> None:
        """Test description contains filter (case-sensitive)"""
        filter_obj = ScalingGroupFilter(
            description=StringFilter(contains="Test"),
        )
        adapter = ScalingGroupGQLAdapter()
        querier = adapter.build_querier(filter=filter_obj)

        assert len(querier.conditions) == 1
        condition_result = querier.conditions[0]()
        assert condition_result is not None

    def test_description_contains_case_insensitive(self) -> None:
        """Test description contains filter (case-insensitive)"""
        filter_obj = ScalingGroupFilter(
            description=StringFilter(i_contains="test"),
        )
        adapter = ScalingGroupGQLAdapter()
        querier = adapter.build_querier(filter=filter_obj)

        assert len(querier.conditions) == 1
        condition_result = querier.conditions[0]()
        assert condition_result is not None

    def test_is_active_filter_true(self) -> None:
        """Test is_active filter (True)"""
        filter_obj = ScalingGroupFilter(is_active=True)
        adapter = ScalingGroupGQLAdapter()
        querier = adapter.build_querier(filter=filter_obj)

        assert len(querier.conditions) == 1
        condition_result = querier.conditions[0]()
        assert condition_result is not None

    def test_is_active_filter_false(self) -> None:
        """Test is_active filter (False)"""
        filter_obj = ScalingGroupFilter(is_active=False)
        adapter = ScalingGroupGQLAdapter()
        querier = adapter.build_querier(filter=filter_obj)

        assert len(querier.conditions) == 1
        condition_result = querier.conditions[0]()
        assert condition_result is not None

    def test_is_public_filter_true(self) -> None:
        """Test is_public filter (True)"""
        filter_obj = ScalingGroupFilter(is_public=True)
        adapter = ScalingGroupGQLAdapter()
        querier = adapter.build_querier(filter=filter_obj)

        assert len(querier.conditions) == 1
        condition_result = querier.conditions[0]()
        assert condition_result is not None

    def test_is_public_filter_false(self) -> None:
        """Test is_public filter (False)"""
        filter_obj = ScalingGroupFilter(is_public=False)
        adapter = ScalingGroupGQLAdapter()
        querier = adapter.build_querier(filter=filter_obj)

        assert len(querier.conditions) == 1
        condition_result = querier.conditions[0]()
        assert condition_result is not None

    def test_driver_filter(self) -> None:
        """Test driver filter"""
        filter_obj = ScalingGroupFilter(driver="static")
        adapter = ScalingGroupGQLAdapter()
        querier = adapter.build_querier(filter=filter_obj)

        assert len(querier.conditions) == 1
        condition_result = querier.conditions[0]()
        assert condition_result is not None

    def test_scheduler_filter(self) -> None:
        """Test scheduler filter"""
        filter_obj = ScalingGroupFilter(scheduler="fifo")
        adapter = ScalingGroupGQLAdapter()
        querier = adapter.build_querier(filter=filter_obj)

        assert len(querier.conditions) == 1
        condition_result = querier.conditions[0]()
        assert condition_result is not None

    def test_use_host_network_filter_true(self) -> None:
        """Test use_host_network filter (True)"""
        filter_obj = ScalingGroupFilter(use_host_network=True)
        adapter = ScalingGroupGQLAdapter()
        querier = adapter.build_querier(filter=filter_obj)

        assert len(querier.conditions) == 1
        condition_result = querier.conditions[0]()
        assert condition_result is not None

    def test_use_host_network_filter_false(self) -> None:
        """Test use_host_network filter (False)"""
        filter_obj = ScalingGroupFilter(use_host_network=False)
        adapter = ScalingGroupGQLAdapter()
        querier = adapter.build_querier(filter=filter_obj)

        assert len(querier.conditions) == 1
        condition_result = querier.conditions[0]()
        assert condition_result is not None

    def test_multiple_filters_combined(self) -> None:
        """Test multiple filters combined"""
        filter_obj = ScalingGroupFilter(
            name=StringFilter(contains="default"),
            is_active=True,
            is_public=True,
            driver="static",
        )
        adapter = ScalingGroupGQLAdapter()
        querier = adapter.build_querier(filter=filter_obj)

        # Should have 4 conditions
        assert len(querier.conditions) == 4
        for condition in querier.conditions:
            assert condition() is not None

    def test_and_logical_operator(self) -> None:
        """Test AND logical operator"""
        filter_obj = ScalingGroupFilter(
            name=StringFilter(contains="default"),
            AND=[
                ScalingGroupFilter(is_active=True),
                ScalingGroupFilter(driver="static"),
            ],
        )
        adapter = ScalingGroupGQLAdapter()
        querier = adapter.build_querier(filter=filter_obj)

        # Should have 3 conditions (name + 2 AND conditions)
        assert len(querier.conditions) == 3
        for condition in querier.conditions:
            assert condition() is not None

    def test_or_logical_operator(self) -> None:
        """Test OR logical operator"""
        filter_obj = ScalingGroupFilter(
            OR=[
                ScalingGroupFilter(name=StringFilter(equals="default")),
                ScalingGroupFilter(name=StringFilter(equals="custom")),
            ],
        )
        adapter = ScalingGroupGQLAdapter()
        querier = adapter.build_querier(filter=filter_obj)

        # Should have 1 combined OR condition
        assert len(querier.conditions) == 1
        condition_result = querier.conditions[0]()
        assert condition_result is not None

    def test_not_logical_operator(self) -> None:
        """Test NOT logical operator"""
        filter_obj = ScalingGroupFilter(
            NOT=[
                ScalingGroupFilter(is_active=False),
            ],
        )
        adapter = ScalingGroupGQLAdapter()
        querier = adapter.build_querier(filter=filter_obj)

        # Should have 1 negated condition
        assert len(querier.conditions) == 1
        condition_result = querier.conditions[0]()
        assert condition_result is not None

    def test_complex_logical_operators(self) -> None:
        """Test complex combination of AND, OR, NOT operators"""
        filter_obj = ScalingGroupFilter(
            name=StringFilter(contains="default"),
            AND=[
                ScalingGroupFilter(is_active=True),
            ],
            OR=[
                ScalingGroupFilter(driver="static"),
                ScalingGroupFilter(scheduler="fifo"),
            ],
            NOT=[
                ScalingGroupFilter(is_public=False),
            ],
        )
        adapter = ScalingGroupGQLAdapter()
        querier = adapter.build_querier(filter=filter_obj)

        # Should have 4 conditions: name + AND + OR (combined) + NOT (negated)
        assert len(querier.conditions) == 4
        for condition in querier.conditions:
            assert condition() is not None

    def test_order_by_name_ascending(self) -> None:
        """Test ordering by name ascending"""
        order_by = [
            ScalingGroupOrderBy(
                field=ScalingGroupOrderField.NAME,
                direction=OrderDirection.ASC,
            )
        ]
        adapter = ScalingGroupGQLAdapter()
        querier = adapter.build_querier(order_by=order_by)

        assert len(querier.orders) == 1
        assert querier.orders[0] is not None

    def test_order_by_name_descending(self) -> None:
        """Test ordering by name descending"""
        order_by = [
            ScalingGroupOrderBy(
                field=ScalingGroupOrderField.NAME,
                direction=OrderDirection.DESC,
            )
        ]
        adapter = ScalingGroupGQLAdapter()
        querier = adapter.build_querier(order_by=order_by)

        assert len(querier.orders) == 1
        assert querier.orders[0] is not None

    def test_order_by_description_ascending(self) -> None:
        """Test ordering by description ascending"""
        order_by = [
            ScalingGroupOrderBy(
                field=ScalingGroupOrderField.DESCRIPTION,
                direction=OrderDirection.ASC,
            )
        ]
        adapter = ScalingGroupGQLAdapter()
        querier = adapter.build_querier(order_by=order_by)

        assert len(querier.orders) == 1
        assert querier.orders[0] is not None

    def test_order_by_description_descending(self) -> None:
        """Test ordering by description descending"""
        order_by = [
            ScalingGroupOrderBy(
                field=ScalingGroupOrderField.DESCRIPTION,
                direction=OrderDirection.DESC,
            )
        ]
        adapter = ScalingGroupGQLAdapter()
        querier = adapter.build_querier(order_by=order_by)

        assert len(querier.orders) == 1
        assert querier.orders[0] is not None

    def test_order_by_created_at_ascending(self) -> None:
        """Test ordering by created_at ascending"""
        order_by = [
            ScalingGroupOrderBy(
                field=ScalingGroupOrderField.CREATED_AT,
                direction=OrderDirection.ASC,
            )
        ]
        adapter = ScalingGroupGQLAdapter()
        querier = adapter.build_querier(order_by=order_by)

        assert len(querier.orders) == 1
        assert querier.orders[0] is not None

    def test_order_by_created_at_descending(self) -> None:
        """Test ordering by created_at descending"""
        order_by = [
            ScalingGroupOrderBy(
                field=ScalingGroupOrderField.CREATED_AT,
                direction=OrderDirection.DESC,
            )
        ]
        adapter = ScalingGroupGQLAdapter()
        querier = adapter.build_querier(order_by=order_by)

        assert len(querier.orders) == 1
        assert querier.orders[0] is not None

    def test_order_by_is_active_ascending(self) -> None:
        """Test ordering by is_active ascending"""
        order_by = [
            ScalingGroupOrderBy(
                field=ScalingGroupOrderField.IS_ACTIVE,
                direction=OrderDirection.ASC,
            )
        ]
        adapter = ScalingGroupGQLAdapter()
        querier = adapter.build_querier(order_by=order_by)

        assert len(querier.orders) == 1
        assert querier.orders[0] is not None

    def test_order_by_is_active_descending(self) -> None:
        """Test ordering by is_active descending"""
        order_by = [
            ScalingGroupOrderBy(
                field=ScalingGroupOrderField.IS_ACTIVE,
                direction=OrderDirection.DESC,
            )
        ]
        adapter = ScalingGroupGQLAdapter()
        querier = adapter.build_querier(order_by=order_by)

        assert len(querier.orders) == 1
        assert querier.orders[0] is not None

    def test_order_by_is_public_ascending(self) -> None:
        """Test ordering by is_public ascending"""
        order_by = [
            ScalingGroupOrderBy(
                field=ScalingGroupOrderField.IS_PUBLIC,
                direction=OrderDirection.ASC,
            )
        ]
        adapter = ScalingGroupGQLAdapter()
        querier = adapter.build_querier(order_by=order_by)

        assert len(querier.orders) == 1
        assert querier.orders[0] is not None

    def test_order_by_is_public_descending(self) -> None:
        """Test ordering by is_public descending"""
        order_by = [
            ScalingGroupOrderBy(
                field=ScalingGroupOrderField.IS_PUBLIC,
                direction=OrderDirection.DESC,
            )
        ]
        adapter = ScalingGroupGQLAdapter()
        querier = adapter.build_querier(order_by=order_by)

        assert len(querier.orders) == 1
        assert querier.orders[0] is not None

    def test_multiple_order_by(self) -> None:
        """Test multiple order by fields"""
        order_by = [
            ScalingGroupOrderBy(
                field=ScalingGroupOrderField.IS_ACTIVE,
                direction=OrderDirection.DESC,
            ),
            ScalingGroupOrderBy(
                field=ScalingGroupOrderField.NAME,
                direction=OrderDirection.ASC,
            ),
        ]
        adapter = ScalingGroupGQLAdapter()
        querier = adapter.build_querier(order_by=order_by)

        assert len(querier.orders) == 2
        assert querier.orders[0] is not None
        assert querier.orders[1] is not None

    def test_pagination_limit_offset(self) -> None:
        """Test pagination with limit and offset"""
        adapter = ScalingGroupGQLAdapter()
        querier = adapter.build_querier(limit=10, offset=5)

        assert querier.pagination is not None
        assert isinstance(querier.pagination, OffsetPagination)
        assert querier.pagination.limit == 10
        assert querier.pagination.offset == 5

    def test_filter_order_pagination_combined(self) -> None:
        """Test filter, order, and pagination all combined"""
        filter_obj = ScalingGroupFilter(
            name=StringFilter(contains="default"),
            is_active=True,
        )
        order_by = [
            ScalingGroupOrderBy(
                field=ScalingGroupOrderField.NAME,
                direction=OrderDirection.ASC,
            )
        ]
        adapter = ScalingGroupGQLAdapter()
        querier = adapter.build_querier(
            filter=filter_obj,
            order_by=order_by,
            limit=20,
            offset=10,
        )

        assert len(querier.conditions) == 2
        assert len(querier.orders) == 1
        assert querier.pagination is not None
        assert isinstance(querier.pagination, OffsetPagination)
        assert querier.pagination.limit == 20
        assert querier.pagination.offset == 10
