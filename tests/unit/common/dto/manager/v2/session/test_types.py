"""Tests for ai.backend.common.dto.manager.v2.session.types module."""

from __future__ import annotations

from ai.backend.common.dto.manager.v2.session.types import (
    OrderDirection,
    SessionOrderField,
    SessionResultEnum,
    SessionStatusEnum,
    SessionStatusFilter,
    SessionTypeEnum,
)


class TestSessionStatusEnum:
    """Tests for SessionStatusEnum values."""

    def test_pending_value(self) -> None:
        assert SessionStatusEnum.PENDING.value == "PENDING"

    def test_scheduled_value(self) -> None:
        assert SessionStatusEnum.SCHEDULED.value == "SCHEDULED"

    def test_preparing_value(self) -> None:
        assert SessionStatusEnum.PREPARING.value == "PREPARING"

    def test_pulling_value(self) -> None:
        assert SessionStatusEnum.PULLING.value == "PULLING"

    def test_prepared_value(self) -> None:
        assert SessionStatusEnum.PREPARED.value == "PREPARED"

    def test_creating_value(self) -> None:
        assert SessionStatusEnum.CREATING.value == "CREATING"

    def test_running_value(self) -> None:
        assert SessionStatusEnum.RUNNING.value == "RUNNING"

    def test_restarting_value(self) -> None:
        assert SessionStatusEnum.RESTARTING.value == "RESTARTING"

    def test_running_degraded_value(self) -> None:
        assert SessionStatusEnum.RUNNING_DEGRADED.value == "RUNNING_DEGRADED"

    def test_terminating_value(self) -> None:
        assert SessionStatusEnum.TERMINATING.value == "TERMINATING"

    def test_terminated_value(self) -> None:
        assert SessionStatusEnum.TERMINATED.value == "TERMINATED"

    def test_error_value(self) -> None:
        assert SessionStatusEnum.ERROR.value == "ERROR"

    def test_cancelled_value(self) -> None:
        assert SessionStatusEnum.CANCELLED.value == "CANCELLED"

    def test_all_members_count(self) -> None:
        assert len(list(SessionStatusEnum)) == 14

    def test_from_string(self) -> None:
        assert SessionStatusEnum("RUNNING") is SessionStatusEnum.RUNNING


class TestSessionTypeEnum:
    """Tests for SessionTypeEnum values."""

    def test_interactive_value(self) -> None:
        assert SessionTypeEnum.INTERACTIVE.value == "interactive"

    def test_batch_value(self) -> None:
        assert SessionTypeEnum.BATCH.value == "batch"

    def test_inference_value(self) -> None:
        assert SessionTypeEnum.INFERENCE.value == "inference"

    def test_system_value(self) -> None:
        assert SessionTypeEnum.SYSTEM.value == "system"

    def test_all_members_count(self) -> None:
        assert len(list(SessionTypeEnum)) == 4


class TestSessionResultEnum:
    """Tests for SessionResultEnum values."""

    def test_undefined_value(self) -> None:
        assert SessionResultEnum.UNDEFINED.value == "undefined"

    def test_success_value(self) -> None:
        assert SessionResultEnum.SUCCESS.value == "success"

    def test_failure_value(self) -> None:
        assert SessionResultEnum.FAILURE.value == "failure"

    def test_cancelled_value(self) -> None:
        assert SessionResultEnum.CANCELLED.value == "cancelled"

    def test_all_members_count(self) -> None:
        assert len(list(SessionResultEnum)) == 4


class TestSessionOrderField:
    """Tests for SessionOrderField values."""

    def test_created_at_value(self) -> None:
        assert SessionOrderField.CREATED_AT.value == "created_at"

    def test_terminated_at_value(self) -> None:
        assert SessionOrderField.TERMINATED_AT.value == "terminated_at"

    def test_status_value(self) -> None:
        assert SessionOrderField.STATUS.value == "status"

    def test_id_value(self) -> None:
        assert SessionOrderField.ID.value == "id"

    def test_name_value(self) -> None:
        assert SessionOrderField.NAME.value == "name"

    def test_all_members_count(self) -> None:
        assert len(list(SessionOrderField)) == 5


class TestOrderDirection:
    """Tests for OrderDirection values."""

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


class TestSessionStatusFilter:
    """Tests for SessionStatusFilter model."""

    def test_default_creation(self) -> None:
        f = SessionStatusFilter()
        assert f.in_ is None
        assert f.not_in is None

    def test_in_filter(self) -> None:
        f = SessionStatusFilter(in_=[SessionStatusEnum.RUNNING, SessionStatusEnum.PENDING])
        assert f.in_ == [SessionStatusEnum.RUNNING, SessionStatusEnum.PENDING]
        assert f.not_in is None

    def test_not_in_filter(self) -> None:
        f = SessionStatusFilter(not_in=[SessionStatusEnum.TERMINATED, SessionStatusEnum.ERROR])
        assert f.in_ is None
        assert f.not_in == [SessionStatusEnum.TERMINATED, SessionStatusEnum.ERROR]

    def test_both_filters(self) -> None:
        f = SessionStatusFilter(
            in_=[SessionStatusEnum.RUNNING],
            not_in=[SessionStatusEnum.TERMINATED],
        )
        assert f.in_ == [SessionStatusEnum.RUNNING]
        assert f.not_in == [SessionStatusEnum.TERMINATED]

    def test_round_trip(self) -> None:
        f = SessionStatusFilter(in_=[SessionStatusEnum.RUNNING])
        json_str = f.model_dump_json()
        restored = SessionStatusFilter.model_validate_json(json_str)
        assert restored.in_ == [SessionStatusEnum.RUNNING]
