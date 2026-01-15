"""Tests for TransitionRecorder."""

from __future__ import annotations

from datetime import UTC, datetime
from uuid import uuid4

import pytest

from ai.backend.common.types import SessionId
from ai.backend.manager.sokovan.recorder import (
    ExecutionRecord,
    NestedPhaseError,
    PhaseRecord,
    RecorderContext,
    RecordPool,
    StepRecord,
    StepStatus,
    StepWithoutPhaseError,
    TransitionRecorder,
)
from ai.backend.manager.sokovan.recorder.types import RecordBuildData


class TestRecorderContext:
    """Tests for RecorderContext class."""

    def test_scope_returns_record_pool(self) -> None:
        """Test that scope() returns a RecordPool with operation name."""
        session_id = SessionId(uuid4())
        with RecorderContext[SessionId].scope("schedule", entity_ids=[session_id]) as pool:
            assert isinstance(pool, RecordPool)
            assert pool.operation == "schedule"

    def test_recorder_created_for_entity(self) -> None:
        """Test that recorder is created for entity_id."""
        session_id = SessionId(uuid4())
        with RecorderContext[SessionId].scope("schedule", entity_ids=[session_id]) as pool:
            recorder = pool.recorder(session_id)
            assert isinstance(recorder, TransitionRecorder)
            assert recorder.entity_id == session_id

    def test_current_pool_raises_outside_scope(self) -> None:
        """Test that current_pool() raises LookupError outside scope."""
        with pytest.raises(LookupError):
            RecorderContext[SessionId].current_pool()

    def test_nested_scopes_are_independent(self) -> None:
        """Test that nested scopes have independent pools."""
        session_id = SessionId(uuid4())
        with RecorderContext[SessionId].scope("schedule", entity_ids=[session_id]) as outer_pool:
            with RecorderContext[SessionId].scope("create", entity_ids=[session_id]) as inner_pool:
                assert inner_pool is not outer_pool
                assert inner_pool.operation == "create"
            assert outer_pool.operation == "schedule"


class TestValidatorPattern:
    """Tests for the validator pattern with phases and multiple steps.

    This simulates the real-world usage where a Validator phase contains
    multiple ValidationRule steps that can independently succeed or fail.
    """

    @pytest.fixture
    def session_id(self) -> SessionId:
        return SessionId(uuid4())

    def test_validator_with_multiple_successful_rules(
        self,
        session_id: SessionId,
    ) -> None:
        """Test validator phase with multiple successful rule steps."""
        with RecorderContext[SessionId].scope("provisioning", entity_ids=[session_id]) as pool:
            recorder = pool.recorder(session_id)
            with recorder.phase("validation"):
                with recorder.step("quota_check", success_detail="Quota OK"):
                    pass
                with recorder.step("resource_limit", success_detail="Limit OK"):
                    pass
                with recorder.step("dependency_check", success_detail="Dependencies OK"):
                    pass

        # Records are built when scope exits
        record = pool.get_record(session_id)
        assert record is not None
        assert len(record.phases) == 1

        phase = record.phases[0]
        assert phase.name == "validation"
        assert phase.status == StepStatus.SUCCESS
        assert len(phase.steps) == 3

        step_names = {s.name for s in phase.steps}
        assert step_names == {"quota_check", "resource_limit", "dependency_check"}

    def test_validator_with_one_failing_rule(
        self,
        session_id: SessionId,
    ) -> None:
        """Test validator phase where step fails and propagates exception."""
        with RecorderContext[SessionId].scope("provisioning", entity_ids=[session_id]) as pool:
            recorder = pool.recorder(session_id)
            with pytest.raises(ValueError, match="Exceeded 8GB memory limit"):
                with recorder.phase("validation"):
                    with recorder.step("quota_check", success_detail="Quota OK"):
                        pass

                    with recorder.step("resource_limit"):
                        raise ValueError("Exceeded 8GB memory limit")

                    # This step won't be reached due to exception
                    with recorder.step("dependency_check", success_detail="Dependencies OK"):
                        pass

        record = pool.get_record(session_id)
        assert record is not None

        phase = record.phases[0]
        assert phase.status == StepStatus.FAILED
        # Only 2 steps recorded (quota_check succeeded, resource_limit failed, dependency_check not reached)
        assert len(phase.steps) == 2

        assert phase.steps[0].name == "quota_check"
        assert phase.steps[0].status == StepStatus.SUCCESS
        assert phase.steps[1].name == "resource_limit"
        assert phase.steps[1].status == StepStatus.FAILED
        assert phase.steps[1].detail == "Exceeded 8GB memory limit"

    def test_nested_phases_raise_error(
        self,
        session_id: SessionId,
    ) -> None:
        """Test that nested phases raise NestedPhaseError."""
        with RecorderContext[SessionId].scope("provisioning", entity_ids=[session_id]) as pool:
            recorder = pool.recorder(session_id)
            with pytest.raises(NestedPhaseError) as exc_info:
                with recorder.phase("provisioner"):
                    with recorder.phase("validation"):
                        pass
            assert exc_info.value.new_phase == "validation"
            assert exc_info.value.active_phase == "provisioner"

    def test_step_without_phase_raises_error(
        self,
        session_id: SessionId,
    ) -> None:
        """Test that step without active phase raises StepWithoutPhaseError."""
        with RecorderContext[SessionId].scope("provisioning", entity_ids=[session_id]) as pool:
            recorder = pool.recorder(session_id)
            with pytest.raises(StepWithoutPhaseError) as exc_info:
                with recorder.step("quota_check"):
                    pass
            assert exc_info.value.step_name == "quota_check"

    def test_multiple_sessions_independent_records(self) -> None:
        """Test that multiple sessions have independent records."""
        session1 = SessionId(uuid4())
        session2 = SessionId(uuid4())

        with RecorderContext[SessionId].scope(
            "provisioning", entity_ids=[session1, session2]
        ) as pool:
            recorder1 = pool.recorder(session1)
            with recorder1.phase("phase_a"):
                with recorder1.step("step1"):
                    pass

            recorder2 = pool.recorder(session2)
            with recorder2.phase("phase_b"):
                with recorder2.step("step2"):
                    pass

        record1 = pool.get_record(session1)
        record2 = pool.get_record(session2)

        assert record1 is not None
        assert record2 is not None
        assert record1.phases[0].name == "phase_a"
        assert record2.phases[0].name == "phase_b"

    def test_phase_recorded_after_exit(
        self,
        session_id: SessionId,
    ) -> None:
        """Test that phases are recorded independently on exit."""
        with RecorderContext[SessionId].scope("provisioning", entity_ids=[session_id]) as pool:
            recorder = pool.recorder(session_id)
            with recorder.phase("phase1"):
                with recorder.step("step1"):
                    pass

            with recorder.phase("phase2"):
                with recorder.step("step2"):
                    pass

        record = pool.get_record(session_id)
        assert record is not None
        assert len(record.phases) == 2
        assert record.phases[0].name == "phase1"
        assert record.phases[0].steps[0].name == "step1"
        assert record.phases[1].name == "phase2"
        assert record.phases[1].steps[0].name == "step2"


class TestStructuredRecords:
    """Tests for the structured record types (ExecutionRecord, PhaseRecord, StepRecord)."""

    @pytest.fixture
    def session_id(self) -> SessionId:
        return SessionId(uuid4())

    def test_get_record_returns_execution_record(
        self,
        session_id: SessionId,
    ) -> None:
        """Test that get_record() returns an ExecutionRecord with proper structure."""
        with RecorderContext[SessionId].scope("schedule", entity_ids=[session_id]) as pool:
            recorder = pool.recorder(session_id)
            with recorder.phase("validation"):
                with recorder.step("quota_check", success_detail="OK"):
                    pass

        record = pool.get_record(session_id)

        assert record is not None
        assert isinstance(record, ExecutionRecord)
        assert len(record.phases) == 1

    def test_phase_record_contains_steps(
        self,
        session_id: SessionId,
    ) -> None:
        """Test that PhaseRecord contains all steps executed within the phase."""
        with RecorderContext[SessionId].scope("schedule", entity_ids=[session_id]) as pool:
            recorder = pool.recorder(session_id)
            with recorder.phase("validation"):
                with recorder.step("quota_check", success_detail="Quota OK"):
                    pass
                with recorder.step("resource_check", success_detail="Resource OK"):
                    pass

        record = pool.get_record(session_id)
        assert record is not None

        phase = record.phases[0]
        assert isinstance(phase, PhaseRecord)
        assert phase.name == "validation"
        assert phase.status == StepStatus.SUCCESS
        assert len(phase.steps) == 2

        step_names = [s.name for s in phase.steps]
        assert step_names == ["quota_check", "resource_check"]

    def test_step_record_structure(
        self,
        session_id: SessionId,
    ) -> None:
        """Test that StepRecord has proper structure."""
        with RecorderContext[SessionId].scope("schedule", entity_ids=[session_id]) as pool:
            recorder = pool.recorder(session_id)
            with recorder.phase("validation"):
                with recorder.step("quota_check", success_detail="Quota OK"):
                    pass

        record = pool.get_record(session_id)
        assert record is not None

        step = record.phases[0].steps[0]
        assert isinstance(step, StepRecord)
        assert step.name == "quota_check"
        assert step.status == StepStatus.SUCCESS
        assert step.detail == "Quota OK"
        assert step.started_at is not None
        assert step.ended_at is not None
        assert step.ended_at >= step.started_at

    def test_phase_status_failed_when_step_fails(
        self,
        session_id: SessionId,
    ) -> None:
        """Test that phase status is FAILED when step raises exception."""
        with RecorderContext[SessionId].scope("schedule", entity_ids=[session_id]) as pool:
            recorder = pool.recorder(session_id)
            with pytest.raises(ValueError, match="Resource limit exceeded"):
                with recorder.phase("validation"):
                    with recorder.step("quota_check", success_detail="OK"):
                        pass
                    with recorder.step("resource_check"):
                        raise ValueError("Resource limit exceeded")

        record = pool.get_record(session_id)
        assert record is not None

        phase = record.phases[0]
        assert phase.status == StepStatus.FAILED
        assert len(phase.steps) == 2
        assert phase.steps[0].status == StepStatus.SUCCESS
        assert phase.steps[1].status == StepStatus.FAILED
        assert phase.steps[1].detail == "Resource limit exceeded"

    def test_multiple_phases_recorded(
        self,
        session_id: SessionId,
    ) -> None:
        """Test that multiple phases are recorded in sequence."""
        with RecorderContext[SessionId].scope("schedule", entity_ids=[session_id]) as pool:
            recorder = pool.recorder(session_id)
            with recorder.phase("validation"):
                with recorder.step("validate"):
                    pass

            with recorder.phase("allocation"):
                with recorder.step("allocate"):
                    pass

        record = pool.get_record(session_id)
        assert record is not None
        assert len(record.phases) == 2
        assert record.phases[0].name == "validation"
        assert record.phases[1].name == "allocation"

    def test_get_all_records_returns_all_entities(self) -> None:
        """Test that get_all_records() returns records for all entities."""
        session1 = SessionId(uuid4())
        session2 = SessionId(uuid4())

        with RecorderContext[SessionId].scope("schedule", entity_ids=[session1, session2]) as pool:
            recorder1 = pool.recorder(session1)
            with recorder1.phase("phase1"):
                with recorder1.step("step1"):
                    pass

            recorder2 = pool.recorder(session2)
            with recorder2.phase("phase2"):
                with recorder2.step("step2"):
                    pass

        all_records = pool.get_all_records()
        assert session1 in all_records
        assert session2 in all_records
        assert all_records[session1].phases[0].name == "phase1"
        assert all_records[session2].phases[0].name == "phase2"

    def test_record_serializable_to_json(
        self,
        session_id: SessionId,
    ) -> None:
        """Test that ExecutionRecord can be serialized to JSON (Pydantic model)."""
        with RecorderContext[SessionId].scope("schedule", entity_ids=[session_id]) as pool:
            recorder = pool.recorder(session_id)
            with recorder.phase("validation"):
                with recorder.step("quota_check", success_detail="OK"):
                    pass

        record = pool.get_record(session_id)
        assert record is not None

        # Pydantic model should be serializable to JSON
        json_data = record.model_dump_json()
        assert "validation" in json_data
        assert "quota_check" in json_data
        assert "success" in json_data

        # Should be deserializable back
        restored = ExecutionRecord.model_validate_json(json_data)
        assert len(restored.phases) == 1
        assert restored.phases[0].name == "validation"


class TestRecorderAPI:
    """Tests for the recorder API via pool.recorder()."""

    @pytest.fixture
    def session_id(self) -> SessionId:
        return SessionId(uuid4())

    def test_recorder_with_string_names(
        self,
        session_id: SessionId,
    ) -> None:
        """Test using recorder with simple string names."""
        with RecorderContext[SessionId].scope("schedule", entity_ids=[session_id]) as pool:
            recorder = pool.recorder(session_id)
            with recorder.phase("validation"):
                with recorder.step("quota_check", success_detail="Quota OK"):
                    pass

        record = pool.get_record(session_id)
        assert record is not None
        assert len(record.phases) == 1
        assert record.phases[0].name == "validation"
        assert record.phases[0].steps[0].name == "quota_check"
        assert record.phases[0].steps[0].detail == "Quota OK"

    def test_recorder_phase_success_detail(
        self,
        session_id: SessionId,
    ) -> None:
        """Test that phase can have success_detail."""
        with RecorderContext[SessionId].scope("schedule", entity_ids=[session_id]) as pool:
            recorder = pool.recorder(session_id)
            with recorder.phase("validation", success_detail="Validation passed"):
                with recorder.step("check"):
                    pass

        record = pool.get_record(session_id)
        assert record is not None
        assert record.phases[0].detail == "Validation passed"

    def test_recorder_multiple_phases(
        self,
        session_id: SessionId,
    ) -> None:
        """Test multiple phases within single recorder."""
        with RecorderContext[SessionId].scope("schedule", entity_ids=[session_id]) as pool:
            recorder = pool.recorder(session_id)
            with recorder.phase("validation"):
                with recorder.step("validate"):
                    pass

            with recorder.phase("allocation"):
                with recorder.step("allocate"):
                    pass

        record = pool.get_record(session_id)
        assert record is not None
        assert len(record.phases) == 2
        assert record.phases[0].name == "validation"
        assert record.phases[1].name == "allocation"

    def test_recorder_failure_handling(
        self,
        session_id: SessionId,
    ) -> None:
        """Test failure handling with recorder."""
        with RecorderContext[SessionId].scope("schedule", entity_ids=[session_id]) as pool:
            recorder = pool.recorder(session_id)
            with pytest.raises(ValueError, match="Resource limit exceeded"):
                with recorder.phase("validation"):
                    with recorder.step("quota_check", success_detail="OK"):
                        pass
                    with recorder.step("resource_check"):
                        raise ValueError("Resource limit exceeded")

        record = pool.get_record(session_id)
        assert record is not None
        assert record.phases[0].status == StepStatus.FAILED
        assert record.phases[0].steps[1].status == StepStatus.FAILED
        assert record.phases[0].steps[1].detail == "Resource limit exceeded"

    def test_recorder_works_standalone(self) -> None:
        """Test that recorder can work standalone."""
        session_id = SessionId(uuid4())
        # Create recorder directly without scope
        recorder = TransitionRecorder(session_id, datetime.now(UTC))
        with recorder.phase("validation"):
            with recorder.step("check"):
                pass

        # Recorder has phases internally
        assert len(recorder._phases) == 1
        assert recorder._phases[0].name == "validation"

    def test_phase_success_detail_on_failure_is_ignored(
        self,
        session_id: SessionId,
    ) -> None:
        """Test that phase success_detail is not used when phase fails."""
        with RecorderContext[SessionId].scope("schedule", entity_ids=[session_id]) as pool:
            recorder = pool.recorder(session_id)
            with pytest.raises(ValueError, match="Check failed"):
                with recorder.phase("validation", success_detail="All passed"):
                    with recorder.step("check"):
                        raise ValueError("Check failed")

        record = pool.get_record(session_id)
        assert record is not None
        phase = record.phases[0]
        assert phase.status == StepStatus.FAILED
        # On failure, detail should be None (not the success_detail)
        assert phase.detail is None


class TestSharedPhases:
    """Tests for shared phases functionality."""

    @pytest.fixture
    def session_id(self) -> SessionId:
        return SessionId(uuid4())

    def test_shared_phase_added_to_pool(self) -> None:
        """Test that shared phases can be added to pool via context manager."""
        session_id = SessionId(uuid4())
        with RecorderContext[SessionId].scope("schedule", entity_ids=[session_id]) as pool:
            with RecorderContext[SessionId].shared_phase(
                "sequencing", success_detail="Sorted by DRF"
            ):
                with RecorderContext[SessionId].shared_step(
                    "drf", success_detail="DRF sequencing applied"
                ):
                    pass

        record = pool.get_record(session_id)
        assert record is not None
        assert len(record.phases) == 1
        assert record.phases[0].name == "sequencing"

    def test_shared_phase_merged_with_entity_phases(
        self,
        session_id: SessionId,
    ) -> None:
        """Test that shared phases are merged with entity phases."""
        with RecorderContext[SessionId].scope("schedule", entity_ids=[session_id]) as pool:
            # Add shared phase
            with RecorderContext[SessionId].shared_phase(
                "sequencing", success_detail="Sorted by DRF"
            ):
                pass

            # Add entity-specific phase
            recorder = pool.recorder(session_id)
            with recorder.phase("validation"):
                with recorder.step("quota_check"):
                    pass

        record = pool.get_record(session_id)
        assert record is not None
        # Should have 2 phases: sequencing (shared) + validation (entity-specific)
        assert len(record.phases) == 2
        phase_names = {p.name for p in record.phases}
        assert phase_names == {"sequencing", "validation"}

    def test_shared_phases_copied_to_multiple_entities(self) -> None:
        """Test that shared phases are copied to all entities."""
        session1 = SessionId(uuid4())
        session2 = SessionId(uuid4())

        with RecorderContext[SessionId].scope("schedule", entity_ids=[session1, session2]) as pool:
            # Add shared phase via context manager
            with RecorderContext[SessionId].shared_phase(
                "sequencing", success_detail="Sorted by DRF"
            ):
                pass

            # Create first entity phases
            recorder1 = pool.recorder(session1)
            with recorder1.phase("validation"):
                with recorder1.step("check1"):
                    pass

            # Create second entity phases
            recorder2 = pool.recorder(session2)
            with recorder2.phase("allocation"):
                with recorder2.step("allocate"):
                    pass

        record1 = pool.get_record(session1)
        record2 = pool.get_record(session2)

        # Both should have sequencing phase
        assert record1 is not None
        assert record2 is not None
        record1_phase_names = {p.name for p in record1.phases}
        record2_phase_names = {p.name for p in record2.phases}
        assert "sequencing" in record1_phase_names
        assert "sequencing" in record2_phase_names
        # But different entity-specific phases
        assert "validation" in record1_phase_names
        assert "allocation" in record2_phase_names

    def test_shared_phases_are_independent_copies(self) -> None:
        """Test that shared phases are independent copies for each entity."""
        session1 = SessionId(uuid4())
        session2 = SessionId(uuid4())

        with RecorderContext[SessionId].scope("schedule", entity_ids=[session1, session2]) as pool:
            with RecorderContext[SessionId].shared_phase("sequencing", success_detail="Sorted"):
                pass

        record1 = pool.get_record(session1)
        record2 = pool.get_record(session2)

        assert record1 is not None
        assert record2 is not None
        # Phases should be independent (not the same object)
        assert record1.phases[0] is not record2.phases[0]

    def test_entity_without_shared_phases(
        self,
        session_id: SessionId,
    ) -> None:
        """Test that entities work normally without shared phases."""
        with RecorderContext[SessionId].scope("schedule", entity_ids=[session_id]) as pool:
            # No shared phases added
            recorder = pool.recorder(session_id)
            with recorder.phase("validation"):
                with recorder.step("check"):
                    pass

        record = pool.get_record(session_id)
        assert record is not None
        # Should have only the entity-specific phase
        assert len(record.phases) == 1
        assert record.phases[0].name == "validation"


class TestSharedPhaseContextManager:
    """Tests for shared_phase() and shared_step() context managers."""

    @pytest.fixture
    def session_id(self) -> SessionId:
        return SessionId(uuid4())

    def test_shared_phase_context_manager_basic(
        self,
        session_id: SessionId,
    ) -> None:
        """Test basic shared_phase() context manager usage."""
        with RecorderContext[SessionId].scope("schedule", entity_ids=[session_id]) as pool:
            with RecorderContext[SessionId].shared_phase("sequencing", success_detail="DRF"):
                pass

            # Create entity phases
            recorder = pool.recorder(session_id)
            with recorder.phase("validation"):
                with recorder.step("check"):
                    pass

        record = pool.get_record(session_id)
        assert record is not None
        assert len(record.phases) == 2
        phase_names = [p.name for p in record.phases]
        assert "sequencing" in phase_names
        sequencing_phase = next(p for p in record.phases if p.name == "sequencing")
        assert sequencing_phase.status == StepStatus.SUCCESS
        assert sequencing_phase.detail == "DRF"

    def test_shared_step_within_shared_phase(
        self,
        session_id: SessionId,
    ) -> None:
        """Test shared_step() within shared_phase()."""
        with RecorderContext[SessionId].scope("schedule", entity_ids=[session_id]) as pool:
            with RecorderContext[SessionId].shared_phase("sequencing", success_detail="Sequenced"):
                with RecorderContext[SessionId].shared_step("drf", success_detail="DRF applied"):
                    pass

        record = pool.get_record(session_id)
        assert record is not None
        phase = record.phases[0]
        assert phase.name == "sequencing"
        assert len(phase.steps) == 1
        assert phase.steps[0].name == "drf"
        assert phase.steps[0].status == StepStatus.SUCCESS
        assert phase.steps[0].detail == "DRF applied"

    def test_shared_phase_failure_handling(
        self,
        session_id: SessionId,
    ) -> None:
        """Test that shared_phase() handles exceptions correctly."""
        with RecorderContext[SessionId].scope("schedule", entity_ids=[session_id]) as pool:
            with pytest.raises(ValueError, match="Sequencing failed"):
                with RecorderContext[SessionId].shared_phase("sequencing", success_detail="OK"):
                    raise ValueError("Sequencing failed")

        record = pool.get_record(session_id)
        assert record is not None
        assert len(record.phases) == 1
        assert record.phases[0].name == "sequencing"
        assert record.phases[0].status == StepStatus.FAILED
        # On failure, detail should be None (not the success_detail)
        assert record.phases[0].detail is None

    def test_shared_step_failure_handling(
        self,
        session_id: SessionId,
    ) -> None:
        """Test that shared_step() handles exceptions correctly."""
        with RecorderContext[SessionId].scope("schedule", entity_ids=[session_id]) as pool:
            with pytest.raises(ValueError, match="Step failed"):
                with RecorderContext[SessionId].shared_phase("sequencing"):
                    with RecorderContext[SessionId].shared_step("drf", success_detail="OK"):
                        raise ValueError("Step failed")

        record = pool.get_record(session_id)
        assert record is not None
        phase = record.phases[0]
        assert phase.status == StepStatus.FAILED
        assert phase.steps[0].status == StepStatus.FAILED
        assert phase.steps[0].detail == "Step failed"

    def test_shared_step_without_phase_raises_error(self) -> None:
        """Test that shared_step() outside shared_phase() raises RuntimeError."""
        session_id = SessionId(uuid4())
        with RecorderContext[SessionId].scope("schedule", entity_ids=[session_id]):
            with pytest.raises(RuntimeError, match="no shared phase is active"):
                with RecorderContext[SessionId].shared_step("drf"):
                    pass

    def test_nested_shared_phases_not_allowed(self) -> None:
        """Test that nested shared_phase() raises RuntimeError."""
        session_id = SessionId(uuid4())
        with RecorderContext[SessionId].scope("schedule", entity_ids=[session_id]):
            with RecorderContext[SessionId].shared_phase("sequencing"):
                with pytest.raises(RuntimeError, match="already active"):
                    with RecorderContext[SessionId].shared_phase("sorting"):
                        pass

    def test_multiple_shared_steps_in_phase(
        self,
        session_id: SessionId,
    ) -> None:
        """Test multiple shared_step() calls within a shared_phase()."""
        with RecorderContext[SessionId].scope("schedule", entity_ids=[session_id]) as pool:
            with RecorderContext[SessionId].shared_phase("sequencing"):
                with RecorderContext[SessionId].shared_step("fifo", success_detail="FIFO"):
                    pass
                with RecorderContext[SessionId].shared_step("drf", success_detail="DRF"):
                    pass

        record = pool.get_record(session_id)
        assert record is not None
        phase = record.phases[0]
        assert len(phase.steps) == 2
        assert phase.steps[0].name == "fifo"
        assert phase.steps[1].name == "drf"

    def test_shared_phase_timestamps_are_recorded(
        self,
        session_id: SessionId,
    ) -> None:
        """Test that shared_phase() and shared_step() record timestamps."""
        with RecorderContext[SessionId].scope("schedule", entity_ids=[session_id]) as pool:
            with RecorderContext[SessionId].shared_phase("sequencing"):
                with RecorderContext[SessionId].shared_step("drf"):
                    pass

        record = pool.get_record(session_id)
        assert record is not None
        phase = record.phases[0]
        assert phase.started_at is not None
        assert phase.ended_at is not None
        assert phase.ended_at >= phase.started_at

        step = phase.steps[0]
        assert step.started_at is not None
        assert step.ended_at is not None
        assert step.ended_at >= step.started_at

    def test_shared_phases_copied_to_multiple_entities(self) -> None:
        """Test that shared phases from context manager are copied to all entities."""
        session1 = SessionId(uuid4())
        session2 = SessionId(uuid4())

        with RecorderContext[SessionId].scope("schedule", entity_ids=[session1, session2]) as pool:
            # Record shared phase using context manager
            with RecorderContext[SessionId].shared_phase("sequencing", success_detail="DRF"):
                with RecorderContext[SessionId].shared_step("drf"):
                    pass

            # Create first entity phases
            recorder1 = pool.recorder(session1)
            with recorder1.phase("validation"):
                with recorder1.step("check1"):
                    pass

            # Create second entity phases
            recorder2 = pool.recorder(session2)
            with recorder2.phase("allocation"):
                with recorder2.step("allocate"):
                    pass

        record1 = pool.get_record(session1)
        record2 = pool.get_record(session2)

        # Both should have sequencing phase
        assert record1 is not None
        assert record2 is not None
        record1_phase_names = {p.name for p in record1.phases}
        record2_phase_names = {p.name for p in record2.phases}
        assert "sequencing" in record1_phase_names
        assert "sequencing" in record2_phase_names
        # Shared phases should be independent copies
        seq1 = next(p for p in record1.phases if p.name == "sequencing")
        seq2 = next(p for p in record2.phases if p.name == "sequencing")
        assert seq1 is not seq2


class TestPhaseOrdering:
    """Tests for phase ordering by started_at timestamp."""

    @pytest.fixture
    def session_id(self) -> SessionId:
        return SessionId(uuid4())

    def test_phases_sorted_by_started_at(
        self,
        session_id: SessionId,
    ) -> None:
        """Test that phases are sorted by started_at when building record."""
        with RecorderContext[SessionId].scope("schedule", entity_ids=[session_id]) as pool:
            # Entity phase first
            recorder = pool.recorder(session_id)
            with recorder.phase("validation"):
                with recorder.step("check"):
                    pass

            # Shared phase after (but should appear based on started_at)
            with RecorderContext[SessionId].shared_phase("sequencing"):
                pass

        record = pool.get_record(session_id)
        assert record is not None
        # Phases should be sorted by started_at
        for i in range(len(record.phases) - 1):
            assert record.phases[i].started_at <= record.phases[i + 1].started_at


class TestRecordBuildData:
    """Tests for RecordBuildData usage."""

    def test_build_execution_record_uses_build_data(self) -> None:
        """Test that build_execution_record uses RecordBuildData correctly."""
        session_id = SessionId(uuid4())
        started_at = datetime.now(UTC)
        recorder = TransitionRecorder(session_id, started_at)

        with recorder.phase("validation"):
            with recorder.step("check"):
                pass

        ended_at = datetime.now(UTC)
        build_data = RecordBuildData(
            started_at=started_at,
            ended_at=ended_at,
            shared_phases=[],
        )

        record = recorder.build_execution_record(build_data)

        assert record.started_at == started_at
        assert record.ended_at == ended_at
        assert len(record.phases) == 1
        assert record.phases[0].name == "validation"
