"""Tests for TransitionRecorder."""

from __future__ import annotations

from uuid import uuid4

import pytest

from ai.backend.common.types import SessionId
from ai.backend.manager.sokovan.scheduler.recorder import (
    PhaseDescriptor,
    RecorderContext,
    StepDescriptor,
    TransitionRecorder,
)


class TestTransitionRecorder:
    """Tests for TransitionRecorder class."""

    @pytest.fixture
    def session_id(self) -> SessionId:
        return SessionId(uuid4())

    @pytest.fixture
    def recorder(self) -> TransitionRecorder:
        return TransitionRecorder("test")

    def test_step_records_started_and_success(
        self,
        recorder: TransitionRecorder,
        session_id: SessionId,
    ) -> None:
        """Test that step() records started and success on normal execution."""
        with recorder.step(
            StepDescriptor(
                session_id=session_id,
                name="check_quota",
                success_detail="Quota validated",
            )
        ):
            pass

        steps = recorder.get_steps(session_id)
        assert len(steps) == 2
        assert steps[0].name == "check_quota"
        assert steps[0].status == "started"
        assert steps[1].name == "check_quota"
        assert steps[1].status == "success"
        assert steps[1].detail == "Quota validated"

    def test_step_records_started_and_failed_on_exception(
        self,
        recorder: TransitionRecorder,
        session_id: SessionId,
    ) -> None:
        """Test that step() records started and failed when exception occurs."""
        with pytest.raises(ValueError, match="Test error"):
            with recorder.step(
                StepDescriptor(
                    session_id=session_id,
                    name="check_quota",
                    success_detail="Should not appear",
                )
            ):
                raise ValueError("Test error")

        steps = recorder.get_steps(session_id)
        assert len(steps) == 2
        assert steps[0].name == "check_quota"
        assert steps[0].status == "started"
        assert steps[1].name == "check_quota"
        assert steps[1].status == "failed"
        assert steps[1].detail == "Test error"

    def test_phase_creates_hierarchical_path(
        self,
        recorder: TransitionRecorder,
        session_id: SessionId,
    ) -> None:
        """Test that phase() creates hierarchical phase paths."""
        with recorder.phase(PhaseDescriptor(session_id=session_id, name="provisioner")):
            with recorder.phase(PhaseDescriptor(session_id=session_id, name="validator")):
                with recorder.step(StepDescriptor(session_id=session_id, name="check_quota")):
                    pass

        steps = recorder.get_steps(session_id)
        assert len(steps) == 2
        assert steps[0].phases == ["provisioner", "validator"]
        assert steps[1].phases == ["provisioner", "validator"]

    def test_phase_resets_after_exit(
        self,
        recorder: TransitionRecorder,
        session_id: SessionId,
    ) -> None:
        """Test that phase path resets after exiting a phase."""
        with recorder.phase(PhaseDescriptor(session_id=session_id, name="provisioner")):
            with recorder.step(StepDescriptor(session_id=session_id, name="step1")):
                pass

        with recorder.step(StepDescriptor(session_id=session_id, name="step2")):
            pass

        steps = recorder.get_steps(session_id)
        assert steps[0].phases == ["provisioner"]
        assert steps[2].phases == []

    def test_get_all_steps_returns_all_sessions(
        self,
        recorder: TransitionRecorder,
    ) -> None:
        """Test that get_all_steps() returns steps for all sessions."""
        session1 = SessionId(uuid4())
        session2 = SessionId(uuid4())

        with recorder.step(StepDescriptor(session_id=session1, name="step1")):
            pass

        with recorder.step(StepDescriptor(session_id=session2, name="step2")):
            pass

        all_steps = recorder.get_all_steps()
        assert session1 in all_steps
        assert session2 in all_steps
        assert len(all_steps[session1]) == 2
        assert len(all_steps[session2]) == 2


class TestRecorderContext:
    """Tests for RecorderContext class."""

    def test_scope_stores_operation(self) -> None:
        """Test that scope() stores the operation name."""
        with RecorderContext.scope("schedule") as recorder:
            assert recorder.operation == "schedule"

    def test_current_returns_active_recorder(self) -> None:
        """Test that current() returns the active recorder."""
        with RecorderContext.scope("schedule") as recorder:
            assert RecorderContext.current() is recorder

    def test_current_raises_outside_scope(self) -> None:
        """Test that current() raises LookupError outside scope."""
        with pytest.raises(LookupError):
            RecorderContext.current()

    def test_nested_scopes_are_independent(self) -> None:
        """Test that nested scopes have independent recorders."""
        with RecorderContext.scope("schedule") as outer_recorder:
            with RecorderContext.scope("create") as inner_recorder:
                assert inner_recorder is not outer_recorder
                assert RecorderContext.current() is inner_recorder
            assert RecorderContext.current() is outer_recorder
