"""Tests for FairShareAdapter order-field conversion."""

from __future__ import annotations

from collections.abc import Sequence
from typing import Any
from unittest.mock import MagicMock

import pytest
from sqlalchemy.orm import InstrumentedAttribute

from ai.backend.common.dto.manager.v2.common import OrderDirection
from ai.backend.common.dto.manager.v2.fair_share.request import (
    DomainFairShareOrder,
    ProjectFairShareOrder,
    UserFairShareOrder,
)
from ai.backend.common.dto.manager.v2.fair_share.types import (
    DomainFairShareOrderField,
    ProjectFairShareOrderField,
    UserFairShareOrderField,
)
from ai.backend.manager.api.adapters.fair_share.adapter import FairShareAdapter
from ai.backend.manager.models.clauses import QueryOrder
from ai.backend.manager.models.domain import DomainRow
from ai.backend.manager.models.fair_share.row import (
    DomainFairShareRow,
    ProjectFairShareRow,
    UserFairShareRow,
)
from ai.backend.manager.models.project import ProjectRow
from ai.backend.manager.models.user import UserRow

_DIRECTIONS = [(OrderDirection.ASC, True), (OrderDirection.DESC, False)]

# (order field, column the field must sort on)
_DOMAIN_CASES: list[tuple[DomainFairShareOrderField, InstrumentedAttribute[Any]]] = [
    (DomainFairShareOrderField.FAIR_SHARE_FACTOR, DomainFairShareRow.fair_share_factor),
    (DomainFairShareOrderField.CREATED_AT, DomainFairShareRow.created_at),
    (DomainFairShareOrderField.DOMAIN_NAME, DomainFairShareRow.domain_name),
    (DomainFairShareOrderField.DOMAIN_IS_ACTIVE, DomainRow.is_active),
]
_DOMAIN_RG_CASES: list[tuple[DomainFairShareOrderField, InstrumentedAttribute[Any]]] = [
    (DomainFairShareOrderField.FAIR_SHARE_FACTOR, DomainFairShareRow.fair_share_factor),
    (DomainFairShareOrderField.CREATED_AT, DomainFairShareRow.created_at),
    (DomainFairShareOrderField.DOMAIN_NAME, DomainRow.name),
    (DomainFairShareOrderField.DOMAIN_IS_ACTIVE, DomainRow.is_active),
]
_PROJECT_CASES: list[tuple[ProjectFairShareOrderField, InstrumentedAttribute[Any]]] = [
    (ProjectFairShareOrderField.FAIR_SHARE_FACTOR, ProjectFairShareRow.fair_share_factor),
    (ProjectFairShareOrderField.CREATED_AT, ProjectFairShareRow.created_at),
    (ProjectFairShareOrderField.PROJECT_NAME, ProjectRow.name),
    (ProjectFairShareOrderField.PROJECT_IS_ACTIVE, ProjectRow.is_active),
]
_USER_CASES: list[tuple[UserFairShareOrderField, InstrumentedAttribute[Any]]] = [
    (UserFairShareOrderField.FAIR_SHARE_FACTOR, UserFairShareRow.fair_share_factor),
    (UserFairShareOrderField.CREATED_AT, UserFairShareRow.created_at),
    (UserFairShareOrderField.USER_USERNAME, UserRow.username),
    (UserFairShareOrderField.USER_EMAIL, UserRow.email),
]


@pytest.fixture
def adapter() -> FairShareAdapter:
    return FairShareAdapter(MagicMock())


def _assert_sorts_on(
    order: QueryOrder, column: InstrumentedAttribute[Any], ascending: bool
) -> None:
    expected = column.asc() if ascending else column.desc()
    assert order.compare(expected)


class TestDomainOrderConversion:
    """Every DomainFairShareOrderField maps to its column, on both surfaces."""

    @pytest.mark.parametrize("direction, ascending", _DIRECTIONS)
    @pytest.mark.parametrize("field, column", _DOMAIN_CASES)
    def test_global_field_sorts_on_column(
        self,
        adapter: FairShareAdapter,
        field: DomainFairShareOrderField,
        column: InstrumentedAttribute[Any],
        direction: OrderDirection,
        ascending: bool,
    ) -> None:
        order = adapter._convert_domain_order(
            DomainFairShareOrder(field=field, direction=direction)
        )
        _assert_sorts_on(order, column, ascending)

    @pytest.mark.parametrize("direction, ascending", _DIRECTIONS)
    @pytest.mark.parametrize("field, column", _DOMAIN_RG_CASES)
    def test_rg_field_sorts_on_column(
        self,
        adapter: FairShareAdapter,
        field: DomainFairShareOrderField,
        column: InstrumentedAttribute[Any],
        direction: OrderDirection,
        ascending: bool,
    ) -> None:
        order = adapter._convert_domain_order_rg(
            DomainFairShareOrder(field=field, direction=direction)
        )
        _assert_sorts_on(order, column, ascending)

    def test_cases_cover_every_field(self) -> None:
        assert {field for field, _ in _DOMAIN_CASES} == set(DomainFairShareOrderField)
        assert {field for field, _ in _DOMAIN_RG_CASES} == set(DomainFairShareOrderField)


class TestProjectOrderConversion:
    """Every ProjectFairShareOrderField maps to its column, on both surfaces."""

    @pytest.mark.parametrize("direction, ascending", _DIRECTIONS)
    @pytest.mark.parametrize("field, column", _PROJECT_CASES)
    def test_global_field_sorts_on_column(
        self,
        adapter: FairShareAdapter,
        field: ProjectFairShareOrderField,
        column: InstrumentedAttribute[Any],
        direction: OrderDirection,
        ascending: bool,
    ) -> None:
        order = adapter._convert_project_order(
            ProjectFairShareOrder(field=field, direction=direction)
        )
        _assert_sorts_on(order, column, ascending)

    @pytest.mark.parametrize("direction, ascending", _DIRECTIONS)
    @pytest.mark.parametrize("field, column", _PROJECT_CASES)
    def test_rg_field_sorts_on_column(
        self,
        adapter: FairShareAdapter,
        field: ProjectFairShareOrderField,
        column: InstrumentedAttribute[Any],
        direction: OrderDirection,
        ascending: bool,
    ) -> None:
        order = adapter._convert_project_order_rg(
            ProjectFairShareOrder(field=field, direction=direction)
        )
        _assert_sorts_on(order, column, ascending)

    def test_cases_cover_every_field(self) -> None:
        assert {field for field, _ in _PROJECT_CASES} == set(ProjectFairShareOrderField)


class TestUserOrderConversion:
    """Every UserFairShareOrderField maps to its column, on both surfaces."""

    @pytest.mark.parametrize("direction, ascending", _DIRECTIONS)
    @pytest.mark.parametrize("field, column", _USER_CASES)
    def test_global_field_sorts_on_column(
        self,
        adapter: FairShareAdapter,
        field: UserFairShareOrderField,
        column: InstrumentedAttribute[Any],
        direction: OrderDirection,
        ascending: bool,
    ) -> None:
        order = adapter._convert_user_order(UserFairShareOrder(field=field, direction=direction))
        _assert_sorts_on(order, column, ascending)

    @pytest.mark.parametrize("direction, ascending", _DIRECTIONS)
    @pytest.mark.parametrize("field, column", _USER_CASES)
    def test_rg_field_sorts_on_column(
        self,
        adapter: FairShareAdapter,
        field: UserFairShareOrderField,
        column: InstrumentedAttribute[Any],
        direction: OrderDirection,
        ascending: bool,
    ) -> None:
        order = adapter._convert_user_order_rg(UserFairShareOrder(field=field, direction=direction))
        _assert_sorts_on(order, column, ascending)

    def test_cases_cover_every_field(self) -> None:
        assert {field for field, _ in _USER_CASES} == set(UserFairShareOrderField)


class TestOrderListConversion:
    """The list converters keep the caller's sort priority."""

    def test_multiple_orders_keep_their_sequence(self, adapter: FairShareAdapter) -> None:
        orders = adapter._convert_project_orders([
            ProjectFairShareOrder(
                field=ProjectFairShareOrderField.PROJECT_NAME,
                direction=OrderDirection.ASC,
            ),
            ProjectFairShareOrder(
                field=ProjectFairShareOrderField.CREATED_AT,
                direction=OrderDirection.DESC,
            ),
        ])

        assert len(orders) == 2
        _assert_sorts_on(orders[0], ProjectRow.name, ascending=True)
        _assert_sorts_on(orders[1], ProjectFairShareRow.created_at, ascending=False)

    def test_empty_input_yields_no_orders(self, adapter: FairShareAdapter) -> None:
        empty: Sequence[list[QueryOrder]] = [
            adapter._convert_domain_orders([]),
            adapter._convert_domain_orders_rg([]),
            adapter._convert_project_orders([]),
            adapter._convert_project_orders_rg([]),
            adapter._convert_user_orders([]),
            adapter._convert_user_orders_rg([]),
        ]
        assert all(orders == [] for orders in empty)
