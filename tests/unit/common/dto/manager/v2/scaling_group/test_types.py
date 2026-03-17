"""Tests for ai.backend.common.dto.manager.v2.scaling_group.types module."""

from __future__ import annotations

from ai.backend.common.dto.manager.v2.scaling_group.types import (
    OrderDirection,
    PreemptionMode,
    PreemptionOrder,
    ScalingGroupOrderField,
    SchedulerType,
)


class TestOrderDirection:
    """Tests for OrderDirection enum."""

    def test_asc_value(self) -> None:
        assert OrderDirection.ASC == "asc"

    def test_desc_value(self) -> None:
        assert OrderDirection.DESC == "desc"

    def test_all_values_present(self) -> None:
        values = {e.value for e in OrderDirection}
        assert values == {"asc", "desc"}


class TestScalingGroupOrderField:
    """Tests for ScalingGroupOrderField enum."""

    def test_name_value(self) -> None:
        assert ScalingGroupOrderField.NAME == "name"

    def test_created_at_value(self) -> None:
        assert ScalingGroupOrderField.CREATED_AT == "created_at"

    def test_is_active_value(self) -> None:
        assert ScalingGroupOrderField.IS_ACTIVE == "is_active"

    def test_all_values_present(self) -> None:
        values = {e.value for e in ScalingGroupOrderField}
        assert values == {"name", "created_at", "is_active"}


class TestSchedulerType:
    """Tests for SchedulerType enum."""

    def test_fifo_value(self) -> None:
        assert SchedulerType.FIFO == "fifo"

    def test_lifo_value(self) -> None:
        assert SchedulerType.LIFO == "lifo"

    def test_drf_value(self) -> None:
        assert SchedulerType.DRF == "drf"

    def test_fair_share_value(self) -> None:
        assert SchedulerType.FAIR_SHARE == "fair-share"

    def test_all_values_present(self) -> None:
        values = {e.value for e in SchedulerType}
        assert values == {"fifo", "lifo", "drf", "fair-share"}


class TestPreemptionMode:
    """Tests for PreemptionMode enum."""

    def test_terminate_value(self) -> None:
        assert PreemptionMode.TERMINATE == "terminate"

    def test_reschedule_value(self) -> None:
        assert PreemptionMode.RESCHEDULE == "reschedule"

    def test_all_values_present(self) -> None:
        values = {e.value for e in PreemptionMode}
        assert values == {"terminate", "reschedule"}


class TestPreemptionOrder:
    """Tests for PreemptionOrder enum."""

    def test_oldest_value(self) -> None:
        assert PreemptionOrder.OLDEST == "oldest"

    def test_newest_value(self) -> None:
        assert PreemptionOrder.NEWEST == "newest"

    def test_all_values_present(self) -> None:
        values = {e.value for e in PreemptionOrder}
        assert values == {"oldest", "newest"}
