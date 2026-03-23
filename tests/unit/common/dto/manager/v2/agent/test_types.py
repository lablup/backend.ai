"""Tests for ai.backend.common.dto.manager.v2.agent.types module."""

from __future__ import annotations

from ai.backend.common.dto.manager.v2.agent.types import (
    AgentOrderField,
    AgentStatusEnum,
    AgentStatusFilter,
    OrderDirection,
)


class TestAgentStatusEnum:
    """Tests for AgentStatusEnum values."""

    def test_alive_value(self) -> None:
        assert AgentStatusEnum.ALIVE.value == "ALIVE"

    def test_lost_value(self) -> None:
        assert AgentStatusEnum.LOST.value == "LOST"

    def test_restarting_value(self) -> None:
        assert AgentStatusEnum.RESTARTING.value == "RESTARTING"

    def test_terminated_value(self) -> None:
        assert AgentStatusEnum.TERMINATED.value == "TERMINATED"

    def test_all_members_count(self) -> None:
        assert len(list(AgentStatusEnum)) == 4

    def test_from_string(self) -> None:
        assert AgentStatusEnum("ALIVE") is AgentStatusEnum.ALIVE

    def test_all_values_are_strings(self) -> None:
        for member in AgentStatusEnum:
            assert isinstance(member.value, str)


class TestAgentOrderField:
    """Tests for AgentOrderField enum."""

    def test_id_value(self) -> None:
        assert AgentOrderField.ID.value == "id"

    def test_status_value(self) -> None:
        assert AgentOrderField.STATUS.value == "status"

    def test_scaling_group_value(self) -> None:
        assert AgentOrderField.SCALING_GROUP.value == "scaling_group"

    def test_all_members_count(self) -> None:
        assert len(list(AgentOrderField)) == 5

    def test_from_string_id(self) -> None:
        assert AgentOrderField("id") is AgentOrderField.ID

    def test_from_string_status(self) -> None:
        assert AgentOrderField("status") is AgentOrderField.STATUS

    def test_from_string_scaling_group(self) -> None:
        assert AgentOrderField("scaling_group") is AgentOrderField.SCALING_GROUP


class TestOrderDirection:
    """Tests for OrderDirection enum."""

    def test_asc_value(self) -> None:
        assert OrderDirection.ASC.value == "ASC"

    def test_desc_value(self) -> None:
        assert OrderDirection.DESC.value == "DESC"

    def test_all_members_count(self) -> None:
        assert len(list(OrderDirection)) == 2

    def test_from_string_asc(self) -> None:
        assert OrderDirection("ASC") is OrderDirection.ASC

    def test_from_string_desc(self) -> None:
        assert OrderDirection("DESC") is OrderDirection.DESC


class TestAgentStatusFilter:
    """Tests for AgentStatusFilter model."""

    def test_all_none_defaults(self) -> None:
        f = AgentStatusFilter()
        assert f.equals is None
        assert f.in_ is None
        assert f.not_equals is None
        assert f.not_in is None

    def test_equals_filter(self) -> None:
        f = AgentStatusFilter(equals=AgentStatusEnum.ALIVE)
        assert f.equals == AgentStatusEnum.ALIVE

    def test_in_filter(self) -> None:
        f = AgentStatusFilter(in_=[AgentStatusEnum.ALIVE, AgentStatusEnum.LOST])
        assert f.in_ == [AgentStatusEnum.ALIVE, AgentStatusEnum.LOST]

    def test_not_equals_filter(self) -> None:
        f = AgentStatusFilter(not_equals=AgentStatusEnum.TERMINATED)
        assert f.not_equals == AgentStatusEnum.TERMINATED

    def test_not_in_filter(self) -> None:
        f = AgentStatusFilter(not_in=[AgentStatusEnum.TERMINATED, AgentStatusEnum.LOST])
        assert f.not_in == [AgentStatusEnum.TERMINATED, AgentStatusEnum.LOST]

    def test_combined_filters(self) -> None:
        f = AgentStatusFilter(
            equals=AgentStatusEnum.ALIVE,
            not_in=[AgentStatusEnum.TERMINATED],
        )
        assert f.equals == AgentStatusEnum.ALIVE
        assert f.not_in == [AgentStatusEnum.TERMINATED]

    def test_round_trip(self) -> None:
        f = AgentStatusFilter(equals=AgentStatusEnum.ALIVE)
        json_str = f.model_dump_json()
        restored = AgentStatusFilter.model_validate_json(json_str)
        assert restored.equals == AgentStatusEnum.ALIVE
