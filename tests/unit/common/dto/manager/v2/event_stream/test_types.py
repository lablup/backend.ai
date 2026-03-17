"""Tests for ai.backend.common.dto.manager.v2.event_stream.types module."""

from __future__ import annotations

from ai.backend.common.dto.manager.streaming.types import (
    BgtaskSSEEventName as OrigBgtaskSSEEventName,
)
from ai.backend.common.dto.manager.streaming.types import (
    SessionEventScope as OrigSessionEventScope,
)
from ai.backend.common.dto.manager.v2.event_stream.types import (
    BgtaskSSEEventName,
    SessionEventScope,
)


class TestSessionEventScope:
    """Tests for SessionEventScope enum re-exported from v1."""

    def test_is_same_object_as_original(self) -> None:
        assert SessionEventScope is OrigSessionEventScope

    def test_session_value(self) -> None:
        assert SessionEventScope.SESSION.value == "session"

    def test_kernel_value(self) -> None:
        assert SessionEventScope.KERNEL.value == "kernel"

    def test_all_values_are_strings(self) -> None:
        for member in SessionEventScope:
            assert isinstance(member.value, str)

    def test_enum_members_count(self) -> None:
        members = list(SessionEventScope)
        assert len(members) == 2

    def test_from_string_session(self) -> None:
        assert SessionEventScope("session") is SessionEventScope.SESSION

    def test_from_string_kernel(self) -> None:
        assert SessionEventScope("kernel") is SessionEventScope.KERNEL


class TestBgtaskSSEEventName:
    """Tests for BgtaskSSEEventName enum re-exported from v1."""

    def test_is_same_object_as_original(self) -> None:
        assert BgtaskSSEEventName is OrigBgtaskSSEEventName

    def test_bgtask_updated_value(self) -> None:
        assert BgtaskSSEEventName.BGTASK_UPDATED.value == "bgtask_updated"

    def test_bgtask_done_value(self) -> None:
        assert BgtaskSSEEventName.BGTASK_DONE.value == "bgtask_done"

    def test_bgtask_cancelled_value(self) -> None:
        assert BgtaskSSEEventName.BGTASK_CANCELLED.value == "bgtask_cancelled"

    def test_bgtask_failed_value(self) -> None:
        assert BgtaskSSEEventName.BGTASK_FAILED.value == "bgtask_failed"

    def test_all_values_are_strings(self) -> None:
        for member in BgtaskSSEEventName:
            assert isinstance(member.value, str)

    def test_enum_members_count(self) -> None:
        members = list(BgtaskSSEEventName)
        assert len(members) == 4

    def test_from_string_updated(self) -> None:
        assert BgtaskSSEEventName("bgtask_updated") is BgtaskSSEEventName.BGTASK_UPDATED

    def test_from_string_done(self) -> None:
        assert BgtaskSSEEventName("bgtask_done") is BgtaskSSEEventName.BGTASK_DONE
