"""
Tests for resource group adapter classes.
Tests conversion from DTO filter objects to repository Querier objects.
"""

from __future__ import annotations

from unittest.mock import MagicMock

from ai.backend.common.dto.manager.query import StringFilter as StringFilterDTO
from ai.backend.common.dto.manager.v2.resource_group.request import (
    ResourceGroupFilter as ResourceGroupFilterDTO,
)
from ai.backend.common.dto.manager.v2.resource_group.request import (
    ResourceGroupOrder as ResourceGroupOrderDTO,
)
from ai.backend.common.dto.manager.v2.resource_group.types import (
    ResourceGroupOrderDirection,
    ResourceGroupOrderField,
)
from ai.backend.manager.api.adapters.pagination import PaginationSpec
from ai.backend.manager.api.adapters.resource_group import ResourceGroupAdapter
from ai.backend.manager.models.scaling_group.conditions import ScalingGroupConditions
from ai.backend.manager.models.scaling_group.orders import ScalingGroupOrders
from ai.backend.manager.models.scaling_group.row import ScalingGroupRow
from ai.backend.manager.repositories.base import OffsetPagination


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
        tiebreaker_order=ScalingGroupRow.name.asc(),
    )


def _make_adapter() -> ResourceGroupAdapter:
    """Create a ResourceGroupAdapter with a mock processors."""
    return ResourceGroupAdapter(processors=MagicMock())


class TestResourceGroupAdapterConvertFilter:
    """Test cases for ResourceGroupAdapter._convert_filter with DTO inputs."""

    def test_empty_filter_produces_no_conditions(self) -> None:
        """Empty filter should produce no query conditions."""
        adapter = _make_adapter()
        filter_dto = ResourceGroupFilterDTO()
        conditions = adapter._convert_filter(filter_dto)
        assert len(conditions) == 0

    def test_name_equals_produces_one_condition(self) -> None:
        """Filter by name equals should produce one condition."""
        adapter = _make_adapter()
        filter_dto = ResourceGroupFilterDTO(name=StringFilterDTO(equals="default"))
        conditions = adapter._convert_filter(filter_dto)
        assert len(conditions) == 1
        condition_result = conditions[0]()
        assert condition_result is not None

    def test_name_contains_produces_one_condition(self) -> None:
        """Filter by name contains should produce one condition."""
        adapter = _make_adapter()
        filter_dto = ResourceGroupFilterDTO(name=StringFilterDTO(contains="def"))
        conditions = adapter._convert_filter(filter_dto)
        assert len(conditions) == 1
        condition_result = conditions[0]()
        assert condition_result is not None

    def test_name_i_contains_produces_one_condition(self) -> None:
        """Filter by name i_contains (case-insensitive contains) should produce one condition."""
        adapter = _make_adapter()
        filter_dto = ResourceGroupFilterDTO(name=StringFilterDTO(i_contains="def"))
        conditions = adapter._convert_filter(filter_dto)
        assert len(conditions) == 1
        condition_result = conditions[0]()
        assert condition_result is not None

    def test_name_i_equals_produces_one_condition(self) -> None:
        """Filter by name i_equals (case-insensitive equals) should produce one condition."""
        adapter = _make_adapter()
        filter_dto = ResourceGroupFilterDTO(name=StringFilterDTO(i_equals="default"))
        conditions = adapter._convert_filter(filter_dto)
        assert len(conditions) == 1
        condition_result = conditions[0]()
        assert condition_result is not None

    def test_is_active_filter_produces_one_condition(self) -> None:
        """Filter by is_active should produce one condition."""
        adapter = _make_adapter()
        filter_dto = ResourceGroupFilterDTO(is_active=True)
        conditions = adapter._convert_filter(filter_dto)
        assert len(conditions) == 1
        condition_result = conditions[0]()
        assert condition_result is not None

    def test_is_public_filter_produces_one_condition(self) -> None:
        """Filter by is_public should produce one condition."""
        adapter = _make_adapter()
        filter_dto = ResourceGroupFilterDTO(is_public=False)
        conditions = adapter._convert_filter(filter_dto)
        assert len(conditions) == 1
        condition_result = conditions[0]()
        assert condition_result is not None

    def test_or_logical_operator_produces_one_combined_condition(self) -> None:
        """OR logical operator should produce one combined condition."""
        adapter = _make_adapter()
        filter_dto = ResourceGroupFilterDTO(
            OR=[
                ResourceGroupFilterDTO(name=StringFilterDTO(equals="default")),
                ResourceGroupFilterDTO(name=StringFilterDTO(equals="custom")),
            ]
        )
        conditions = adapter._convert_filter(filter_dto)
        # Should have 1 combined OR condition
        assert len(conditions) == 1
        condition_result = conditions[0]()
        assert condition_result is not None

    def test_not_logical_operator_produces_one_negated_condition(self) -> None:
        """NOT logical operator should produce one negated condition."""
        adapter = _make_adapter()
        filter_dto = ResourceGroupFilterDTO(NOT=[ResourceGroupFilterDTO(is_active=False)])
        conditions = adapter._convert_filter(filter_dto)
        assert len(conditions) == 1
        condition_result = conditions[0]()
        assert condition_result is not None

    def test_and_logical_operator_produces_multiple_conditions(self) -> None:
        """AND logical operator should extend conditions list."""
        adapter = _make_adapter()
        filter_dto = ResourceGroupFilterDTO(
            AND=[
                ResourceGroupFilterDTO(name=StringFilterDTO(equals="default")),
                ResourceGroupFilterDTO(is_active=True),
            ]
        )
        conditions = adapter._convert_filter(filter_dto)
        # AND appends each sub-filter's conditions: name=1, is_active=1 → 2 total
        assert len(conditions) == 2


class TestResourceGroupAdapterConvertOrders:
    """Test cases for ResourceGroupAdapter._convert_orders with DTO inputs."""

    def test_order_by_name_ascending(self) -> None:
        """Order by name ascending should produce one order expression."""
        adapter = _make_adapter()
        orders = adapter._convert_orders([
            ResourceGroupOrderDTO(
                field=ResourceGroupOrderField.NAME, direction=ResourceGroupOrderDirection.ASC
            )
        ])
        assert len(orders) == 1
        assert orders[0] is not None

    def test_order_by_name_descending(self) -> None:
        """Order by name descending should produce one order expression."""
        adapter = _make_adapter()
        orders = adapter._convert_orders([
            ResourceGroupOrderDTO(
                field=ResourceGroupOrderField.NAME, direction=ResourceGroupOrderDirection.DESC
            )
        ])
        assert len(orders) == 1
        assert orders[0] is not None

    def test_order_by_created_at(self) -> None:
        """Order by created_at should produce one order expression."""
        adapter = _make_adapter()
        orders = adapter._convert_orders([
            ResourceGroupOrderDTO(
                field=ResourceGroupOrderField.CREATED_AT, direction=ResourceGroupOrderDirection.DESC
            )
        ])
        assert len(orders) == 1
        assert orders[0] is not None

    def test_order_by_is_active(self) -> None:
        """Order by is_active should produce one order expression."""
        adapter = _make_adapter()
        orders = adapter._convert_orders([
            ResourceGroupOrderDTO(
                field=ResourceGroupOrderField.IS_ACTIVE, direction=ResourceGroupOrderDirection.ASC
            )
        ])
        assert len(orders) == 1
        assert orders[0] is not None


class TestResourceGroupAdapterBuildQuerier:
    """Test cases for ResourceGroupAdapter._build_querier."""

    def test_empty_querier_has_default_pagination(self) -> None:
        """Test building querier with no filters or orders returns default pagination."""
        adapter = _make_adapter()
        spec = _get_pagination_spec()
        querier = adapter._build_querier(
            conditions=[],
            orders=[],
            pagination_spec=spec,
        )
        assert len(querier.conditions) == 0
        # Default order + tiebreaker order
        assert len(querier.orders) == 2
        assert querier.pagination is not None
        assert isinstance(querier.pagination, OffsetPagination)

    def test_pagination_limit_offset(self) -> None:
        """Test pagination with limit and offset."""
        adapter = _make_adapter()
        spec = _get_pagination_spec()
        querier = adapter._build_querier(
            conditions=[],
            orders=[],
            pagination_spec=spec,
            limit=10,
            offset=5,
        )
        assert querier.pagination is not None
        assert isinstance(querier.pagination, OffsetPagination)
        assert querier.pagination.limit == 10
        assert querier.pagination.offset == 5
