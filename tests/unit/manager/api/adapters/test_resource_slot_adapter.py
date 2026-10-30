from __future__ import annotations

import uuid
from typing import Any
from unittest.mock import MagicMock

import pytest
from sqlalchemy.dialects import postgresql

from ai.backend.common.dto.manager.query import StringFilter, UUIDFilter
from ai.backend.common.dto.manager.v2.resource_slot.request import (
    ResourceAllocationFilter,
    ResourceSlotTypeFilter,
)
from ai.backend.manager.api.adapters.resource_slot.adapter import ResourceSlotAdapter
from ai.backend.manager.models.clauses import QueryCondition
from ai.backend.manager.models.condition_utils import combine_conditions_and

_pg_dialect_cls: Any = postgresql.dialect
_PG_DIALECT = _pg_dialect_cls()


def _to_sql(conditions: list[QueryCondition]) -> str:
    return str(
        combine_conditions_and(conditions)().compile(
            dialect=_PG_DIALECT, compile_kwargs={"literal_binds": True}
        )
    )


@pytest.fixture
def adapter() -> ResourceSlotAdapter:
    return ResourceSlotAdapter(MagicMock(), MagicMock(), MagicMock())


class TestConvertSlotTypeFilter:
    @pytest.mark.parametrize(
        ("filter", "expected"),
        [
            (
                ResourceSlotTypeFilter(slot_name=StringFilter(equals="cuda.device")),
                "resource_slot_types.slot_name = 'cuda.device'",
            ),
            (
                ResourceSlotTypeFilter(slot_type=StringFilter(equals="count")),
                "resource_slot_types.slot_type = 'count'",
            ),
            (
                ResourceSlotTypeFilter(display_name=StringFilter(equals="GPU")),
                "resource_slot_types.display_name = 'GPU'",
            ),
        ],
    )
    def test_each_field_narrows(
        self, adapter: ResourceSlotAdapter, filter: ResourceSlotTypeFilter, expected: str
    ) -> None:
        assert _to_sql(adapter._convert_slot_type_filter(filter)) == expected

    def test_and_items_join_the_outer_conditions(self, adapter: ResourceSlotAdapter) -> None:
        filter = ResourceSlotTypeFilter(
            slot_type=StringFilter(equals="count"),
            AND=[
                ResourceSlotTypeFilter(slot_name=StringFilter(equals="cpu")),
                ResourceSlotTypeFilter(display_name=StringFilter(equals="CPU")),
            ],
        )
        assert _to_sql(adapter._convert_slot_type_filter(filter)) == (
            "resource_slot_types.slot_type = 'count'"
            " AND resource_slot_types.slot_name = 'cpu'"
            " AND resource_slot_types.display_name = 'CPU'"
        )

    def test_or_item_combines_its_fields_with_and(self, adapter: ResourceSlotAdapter) -> None:
        filter = ResourceSlotTypeFilter(
            OR=[
                ResourceSlotTypeFilter(
                    slot_name=StringFilter(equals="cpu"),
                    slot_type=StringFilter(equals="count"),
                ),
                ResourceSlotTypeFilter(slot_name=StringFilter(equals="mem")),
            ]
        )
        assert _to_sql(adapter._convert_slot_type_filter(filter)) == (
            "resource_slot_types.slot_name = 'cpu' AND resource_slot_types.slot_type = 'count'"
            " OR resource_slot_types.slot_name = 'mem'"
        )

    def test_not_negates_each_item_on_its_own(self, adapter: ResourceSlotAdapter) -> None:
        filter = ResourceSlotTypeFilter(
            NOT=[
                ResourceSlotTypeFilter(
                    slot_name=StringFilter(equals="cpu"),
                    slot_type=StringFilter(equals="count"),
                ),
                ResourceSlotTypeFilter(slot_name=StringFilter(equals="mem")),
            ]
        )
        assert _to_sql(adapter._convert_slot_type_filter(filter)) == (
            "NOT (resource_slot_types.slot_name = 'cpu'"
            " AND resource_slot_types.slot_type = 'count')"
            " AND resource_slot_types.slot_name != 'mem'"
        )


class TestConvertResourceAllocationFilter:
    _KERNEL_ID = uuid.UUID("11111111-1111-1111-1111-111111111111")

    def test_and_items_join_the_outer_conditions(self, adapter: ResourceSlotAdapter) -> None:
        filter = ResourceAllocationFilter(
            slot_name=StringFilter(equals="cpu"),
            AND=[ResourceAllocationFilter(kernel_id=UUIDFilter(equals=self._KERNEL_ID))],
        )
        assert _to_sql(adapter._convert_resource_allocation_filter(filter)) == (
            "resource_allocations.slot_name = 'cpu'"
            f" AND resource_allocations.kernel_id = '{self._KERNEL_ID}'"
        )

    def test_or_item_combines_its_fields_with_and(self, adapter: ResourceSlotAdapter) -> None:
        filter = ResourceAllocationFilter(
            OR=[
                ResourceAllocationFilter(
                    slot_name=StringFilter(equals="cpu"),
                    kernel_id=UUIDFilter(equals=self._KERNEL_ID),
                ),
                ResourceAllocationFilter(slot_name=StringFilter(equals="mem")),
            ]
        )
        assert _to_sql(adapter._convert_resource_allocation_filter(filter)) == (
            "resource_allocations.slot_name = 'cpu'"
            f" AND resource_allocations.kernel_id = '{self._KERNEL_ID}'"
            " OR resource_allocations.slot_name = 'mem'"
        )

    def test_not_negates_each_item_on_its_own(self, adapter: ResourceSlotAdapter) -> None:
        filter = ResourceAllocationFilter(
            NOT=[
                ResourceAllocationFilter(
                    slot_name=StringFilter(equals="cpu"),
                    kernel_id=UUIDFilter(equals=self._KERNEL_ID),
                ),
                ResourceAllocationFilter(slot_name=StringFilter(equals="mem")),
            ]
        )
        assert _to_sql(adapter._convert_resource_allocation_filter(filter)) == (
            "NOT (resource_allocations.slot_name = 'cpu'"
            f" AND resource_allocations.kernel_id = '{self._KERNEL_ID}')"
            " AND resource_allocations.slot_name != 'mem'"
        )
