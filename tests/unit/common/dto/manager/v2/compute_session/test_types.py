"""Tests for ai.backend.common.dto.manager.v2.compute_session.types module."""

from __future__ import annotations

from ai.backend.common.dto.manager.v2.compute_session.types import (
    ComputeSessionFilter,
    ComputeSessionOrder,
    ComputeSessionOrderField,
    OrderDirection,
)


class TestComputeSessionOrderField:
    """Tests for ComputeSessionOrderField enum."""

    def test_created_at_value(self) -> None:
        assert ComputeSessionOrderField.CREATED_AT.value == "created_at"

    def test_id_value(self) -> None:
        assert ComputeSessionOrderField.ID.value == "id"

    def test_all_members_count(self) -> None:
        assert len(list(ComputeSessionOrderField)) == 2

    def test_from_string_created_at(self) -> None:
        assert ComputeSessionOrderField("created_at") is ComputeSessionOrderField.CREATED_AT

    def test_from_string_id(self) -> None:
        assert ComputeSessionOrderField("id") is ComputeSessionOrderField.ID


class TestOrderDirection:
    """Tests for OrderDirection enum."""

    def test_asc_value(self) -> None:
        assert OrderDirection.ASC.value == "asc"

    def test_desc_value(self) -> None:
        assert OrderDirection.DESC.value == "desc"

    def test_all_members_count(self) -> None:
        assert len(list(OrderDirection)) == 2

    def test_from_string_asc(self) -> None:
        assert OrderDirection("asc") is OrderDirection.ASC

    def test_from_string_desc(self) -> None:
        assert OrderDirection("desc") is OrderDirection.DESC


class TestComputeSessionFilter:
    """Tests for ComputeSessionFilter model."""

    def test_all_none_defaults(self) -> None:
        f = ComputeSessionFilter()
        assert f.status is None
        assert f.name is None
        assert f.access_key is None
        assert f.domain_name is None
        assert f.scaling_group_name is None

    def test_with_status_list(self) -> None:
        f = ComputeSessionFilter(status=["RUNNING", "PENDING"])
        assert f.status == ["RUNNING", "PENDING"]

    def test_round_trip(self) -> None:
        f = ComputeSessionFilter(status=["RUNNING"])
        json_str = f.model_dump_json()
        restored = ComputeSessionFilter.model_validate_json(json_str)
        assert restored.status == ["RUNNING"]


class TestComputeSessionOrder:
    """Tests for ComputeSessionOrder model."""

    def test_default_direction_is_desc(self) -> None:
        order = ComputeSessionOrder(field=ComputeSessionOrderField.CREATED_AT)
        assert order.direction == OrderDirection.DESC

    def test_asc_direction(self) -> None:
        order = ComputeSessionOrder(
            field=ComputeSessionOrderField.ID,
            direction=OrderDirection.ASC,
        )
        assert order.field == ComputeSessionOrderField.ID
        assert order.direction == OrderDirection.ASC

    def test_round_trip(self) -> None:
        order = ComputeSessionOrder(
            field=ComputeSessionOrderField.CREATED_AT,
            direction=OrderDirection.DESC,
        )
        json_str = order.model_dump_json()
        restored = ComputeSessionOrder.model_validate_json(json_str)
        assert restored.field == ComputeSessionOrderField.CREATED_AT
        assert restored.direction == OrderDirection.DESC
