"""Tests for ai.backend.common.dto.manager.v2.scheduling_history.types module."""

from __future__ import annotations

import json
from datetime import UTC, datetime

from ai.backend.common.dto.manager.v2.scheduling_history.types import (
    DeploymentHistoryOrderField,
    OrderDirection,
    RouteHistoryOrderField,
    SchedulingResultType,
    SessionHistoryOrderField,
    SubStepResultInfo,
)


class TestOrderDirection:
    """Tests for OrderDirection enum."""

    def test_asc_value(self) -> None:
        assert OrderDirection.ASC.value == "asc"

    def test_desc_value(self) -> None:
        assert OrderDirection.DESC.value == "desc"

    def test_enum_members_count(self) -> None:
        assert len(list(OrderDirection)) == 2

    def test_from_string_asc(self) -> None:
        assert OrderDirection("asc") is OrderDirection.ASC

    def test_from_string_desc(self) -> None:
        assert OrderDirection("desc") is OrderDirection.DESC


class TestSchedulingResultType:
    """Tests for SchedulingResultType enum."""

    def test_success_value(self) -> None:
        assert SchedulingResultType.SUCCESS.value == "SUCCESS"

    def test_failure_value(self) -> None:
        assert SchedulingResultType.FAILURE.value == "FAILURE"

    def test_stale_value(self) -> None:
        assert SchedulingResultType.STALE.value == "STALE"

    def test_need_retry_value(self) -> None:
        assert SchedulingResultType.NEED_RETRY.value == "NEED_RETRY"

    def test_expired_value(self) -> None:
        assert SchedulingResultType.EXPIRED.value == "EXPIRED"

    def test_give_up_value(self) -> None:
        assert SchedulingResultType.GIVE_UP.value == "GIVE_UP"

    def test_skipped_value(self) -> None:
        assert SchedulingResultType.SKIPPED.value == "SKIPPED"

    def test_enum_has_seven_members(self) -> None:
        assert len(list(SchedulingResultType)) == 7

    def test_all_values_are_strings(self) -> None:
        for member in SchedulingResultType:
            assert isinstance(member.value, str)

    def test_from_string_success(self) -> None:
        assert SchedulingResultType("SUCCESS") is SchedulingResultType.SUCCESS

    def test_from_string_need_retry(self) -> None:
        assert SchedulingResultType("NEED_RETRY") is SchedulingResultType.NEED_RETRY


class TestSessionHistoryOrderField:
    """Tests for SessionHistoryOrderField enum."""

    def test_created_at_value(self) -> None:
        assert SessionHistoryOrderField.CREATED_AT.value == "created_at"

    def test_updated_at_value(self) -> None:
        assert SessionHistoryOrderField.UPDATED_AT.value == "updated_at"

    def test_enum_members_count(self) -> None:
        assert len(list(SessionHistoryOrderField)) == 2


class TestDeploymentHistoryOrderField:
    """Tests for DeploymentHistoryOrderField enum."""

    def test_created_at_value(self) -> None:
        assert DeploymentHistoryOrderField.CREATED_AT.value == "created_at"

    def test_updated_at_value(self) -> None:
        assert DeploymentHistoryOrderField.UPDATED_AT.value == "updated_at"

    def test_enum_members_count(self) -> None:
        assert len(list(DeploymentHistoryOrderField)) == 2


class TestRouteHistoryOrderField:
    """Tests for RouteHistoryOrderField enum."""

    def test_created_at_value(self) -> None:
        assert RouteHistoryOrderField.CREATED_AT.value == "created_at"

    def test_updated_at_value(self) -> None:
        assert RouteHistoryOrderField.UPDATED_AT.value == "updated_at"

    def test_enum_members_count(self) -> None:
        assert len(list(RouteHistoryOrderField)) == 2


class TestSubStepResultInfo:
    """Tests for SubStepResultInfo Pydantic model."""

    def test_basic_creation_with_all_fields(self) -> None:
        now = datetime.now(tz=UTC)
        info = SubStepResultInfo(
            step="check_resources",
            result="success",
            error_code=None,
            message=None,
            started_at=now,
            ended_at=now,
        )
        assert info.step == "check_resources"
        assert info.result == "success"
        assert info.error_code is None
        assert info.message is None

    def test_creation_with_error_fields(self) -> None:
        now = datetime.now(tz=UTC)
        info = SubStepResultInfo(
            step="allocate_kernel",
            result="failure",
            error_code="ERR_001",
            message="Insufficient resources",
            started_at=now,
            ended_at=now,
        )
        assert info.error_code == "ERR_001"
        assert info.message == "Insufficient resources"

    def test_serialization_round_trip(self) -> None:
        now = datetime.now(tz=UTC)
        info = SubStepResultInfo(
            step="check",
            result="success",
            error_code=None,
            message=None,
            started_at=now,
            ended_at=now,
        )
        json_str = info.model_dump_json()
        restored = SubStepResultInfo.model_validate_json(json_str)
        assert restored.step == info.step
        assert restored.result == info.result
        assert restored.error_code is None
        assert restored.message is None

    def test_model_dump_json(self) -> None:
        now = datetime.now(tz=UTC)
        info = SubStepResultInfo(
            step="my_step",
            result="success",
            error_code="ERR",
            message="msg",
            started_at=now,
            ended_at=now,
        )
        parsed = json.loads(info.model_dump_json())
        assert parsed["step"] == "my_step"
        assert parsed["result"] == "success"
        assert parsed["error_code"] == "ERR"
        assert parsed["message"] == "msg"
