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


class TestRecorderContext:
    """Tests for RecorderContext class."""

    def test_scope_returns_record_pool(self) -> None:
        """Test that scope() returns a RecordPool with operation name."""
        with RecorderContext[SessionId].scope("schedule") as pool:
            assert isinstance(pool, RecordPool)
            assert pool.operation == "schedule"

    def test_entity_creates_recorder(self) -> None:
        """Test that entity() creates a TransitionRecorder."""
        session_id = SessionId(uuid4())
        with RecorderContext[SessionId].scope("schedule"):
            with RecorderContext[SessionId].entity(session_id):
                recorder = RecorderContext[SessionId].current_recorder()
                assert isinstance(recorder, TransitionRecorder)
                assert recorder.entity_id == session_id

    def test_current_recorder_raises_outside_entity(self) -> None:
        """Test that current_recorder() raises LookupError outside entity context."""
        with RecorderContext[SessionId].scope("schedule"):
            with pytest.raises(LookupError):
                RecorderContext[SessionId].current_recorder()

    def test_current_recorder_raises_outside_scope(self) -> None:
        """Test that current_recorder() raises LookupError outside scope."""
        with pytest.raises(LookupError):
            RecorderContext[SessionId].current_recorder()

    def test_nested_scopes_are_independent(self) -> None:
        """Test that nested scopes have independent pools."""
        session_id = SessionId(uuid4())
        with RecorderContext[SessionId].scope("schedule") as outer_pool:
            with RecorderContext[SessionId].scope("create") as inner_pool:
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
        with RecorderContext[SessionId].scope("provisioning") as pool:
            with RecorderContext[SessionId].entity(session_id):
                recorder = RecorderContext[SessionId].current_recorder()
                with recorder.phase("validation"):
                    with recorder.step("quota_check", success_detail="Quota OK"):
                        pass
                    with recorder.step("resource_limit", success_detail="Limit OK"):
                        pass
                    with recorder.step("dependency_check", success_detail="Dependencies OK"):
                        pass

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
        with RecorderContext[SessionId].scope("provisioning") as pool:
            with RecorderContext[SessionId].entity(session_id):
                recorder = RecorderContext[SessionId].current_recorder()
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
        with RecorderContext[SessionId].scope("provisioning"):
            with RecorderContext[SessionId].entity(session_id):
                recorder = RecorderContext[SessionId].current_recorder()
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
        with RecorderContext[SessionId].scope("provisioning"):
            with RecorderContext[SessionId].entity(session_id):
                recorder = RecorderContext[SessionId].current_recorder()
                with pytest.raises(StepWithoutPhaseError) as exc_info:
                    with recorder.step("quota_check"):
                        pass
                assert exc_info.value.step_name == "quota_check"

    def test_multiple_sessions_independent_records(self) -> None:
        """Test that multiple sessions have independent records."""
        session1 = SessionId(uuid4())
        session2 = SessionId(uuid4())

        with RecorderContext[SessionId].scope("provisioning") as pool:
            with RecorderContext[SessionId].entity(session1):
                recorder = RecorderContext[SessionId].current_recorder()
                with recorder.phase("phase_a"):
                    with recorder.step("step1"):
                        pass

            with RecorderContext[SessionId].entity(session2):
                recorder = RecorderContext[SessionId].current_recorder()
                with recorder.phase("phase_b"):
                    with recorder.step("step2"):
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
        with RecorderContext[SessionId].scope("provisioning") as pool:
            with RecorderContext[SessionId].entity(session_id):
                recorder = RecorderContext[SessionId].current_recorder()
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
        with RecorderContext[SessionId].scope("schedule") as pool:
            with RecorderContext[SessionId].entity(session_id):
                recorder = RecorderContext[SessionId].current_recorder()
                with recorder.phase("validation"):
                    with recorder.step("quota_check", success_detail="OK"):
                        pass

            record = pool.get_record(session_id)

            assert record is not None
            assert isinstance(record, ExecutionRecord)
            assert record.operation == "schedule"
            assert len(record.phases) == 1

    def test_phase_record_contains_steps(
        self,
        session_id: SessionId,
    ) -> None:
        """Test that PhaseRecord contains all steps executed within the phase."""
        with RecorderContext[SessionId].scope("schedule") as pool:
            with RecorderContext[SessionId].entity(session_id):
                recorder = RecorderContext[SessionId].current_recorder()
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
        with RecorderContext[SessionId].scope("schedule") as pool:
            with RecorderContext[SessionId].entity(session_id):
                recorder = RecorderContext[SessionId].current_recorder()
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
        with RecorderContext[SessionId].scope("schedule") as pool:
            with RecorderContext[SessionId].entity(session_id):
                recorder = RecorderContext[SessionId].current_recorder()
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
        with RecorderContext[SessionId].scope("schedule") as pool:
            with RecorderContext[SessionId].entity(session_id):
                recorder = RecorderContext[SessionId].current_recorder()
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

    def test_execution_record_status_success_when_all_phases_succeed(
        self,
        session_id: SessionId,
    ) -> None:
        """Test that ExecutionRecord.status is SUCCESS when all phases succeed."""
        with RecorderContext[SessionId].scope("schedule") as pool:
            with RecorderContext[SessionId].entity(session_id):
                recorder = RecorderContext[SessionId].current_recorder()
                with recorder.phase("validation"):
                    with recorder.step("validate"):
                        pass

                with recorder.phase("allocation"):
                    with recorder.step("allocate"):
                        pass

            record = pool.get_record(session_id)
            assert record is not None
            assert record.status == StepStatus.SUCCESS

    def test_execution_record_status_failed_when_entity_context_fails(
        self,
        session_id: SessionId,
    ) -> None:
        """Test that ExecutionRecord.status is FAILED when entity context exits with exception."""
        with RecorderContext[SessionId].scope("schedule") as pool:
            with pytest.raises(ValueError, match="Allocation failed"):
                with RecorderContext[SessionId].entity(session_id):
                    recorder = RecorderContext[SessionId].current_recorder()
                    with recorder.phase("validation"):
                        with recorder.step("validate"):
                            pass

                    with recorder.phase("allocation"):
                        with recorder.step("allocate"):
                            raise ValueError("Allocation failed")

            record = pool.get_record(session_id)
            assert record is not None
            assert record.status == StepStatus.FAILED

    def test_get_all_records_returns_all_entities(self) -> None:
        """Test that get_all_records() returns records for all entities."""
        session1 = SessionId(uuid4())
        session2 = SessionId(uuid4())

        with RecorderContext[SessionId].scope("schedule") as pool:
            with RecorderContext[SessionId].entity(session1):
                recorder = RecorderContext[SessionId].current_recorder()
                with recorder.phase("phase1"):
                    with recorder.step("step1"):
                        pass

            with RecorderContext[SessionId].entity(session2):
                recorder = RecorderContext[SessionId].current_recorder()
                with recorder.phase("phase2"):
                    with recorder.step("step2"):
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
        with RecorderContext[SessionId].scope("schedule") as pool:
            with RecorderContext[SessionId].entity(session_id):
                recorder = RecorderContext[SessionId].current_recorder()
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
            assert restored.operation == "schedule"
            assert len(restored.phases) == 1
            assert restored.phases[0].name == "validation"


class TestEntityContextAPI:
    """Tests for the entity context manager API."""

    @pytest.fixture
    def session_id(self) -> SessionId:
        return SessionId(uuid4())

    def test_entity_context_with_string_names(
        self,
        session_id: SessionId,
    ) -> None:
        """Test using entity context with simple string names."""
        with RecorderContext[SessionId].scope("schedule") as pool:
            with RecorderContext[SessionId].entity(session_id):
                recorder = RecorderContext[SessionId].current_recorder()
                with recorder.phase("validation"):
                    with recorder.step("quota_check", success_detail="Quota OK"):
                        pass

            record = pool.get_record(session_id)
            assert record is not None
            assert len(record.phases) == 1
            assert record.phases[0].name == "validation"
            assert record.phases[0].steps[0].name == "quota_check"
            assert record.phases[0].steps[0].detail == "Quota OK"

    def test_entity_context_phase_success_detail(
        self,
        session_id: SessionId,
    ) -> None:
        """Test that phase can have success_detail."""
        with RecorderContext[SessionId].scope("schedule") as pool:
            with RecorderContext[SessionId].entity(session_id):
                recorder = RecorderContext[SessionId].current_recorder()
                with recorder.phase("validation", success_detail="Validation passed"):
                    with recorder.step("check"):
                        pass

            record = pool.get_record(session_id)
            assert record is not None
            assert record.phases[0].detail == "Validation passed"

    def test_entity_context_multiple_phases(
        self,
        session_id: SessionId,
    ) -> None:
        """Test multiple phases within single entity context."""
        with RecorderContext[SessionId].scope("schedule") as pool:
            with RecorderContext[SessionId].entity(session_id):
                recorder = RecorderContext[SessionId].current_recorder()
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

    def test_entity_context_failure_handling(
        self,
        session_id: SessionId,
    ) -> None:
        """Test failure handling with entity context."""
        with RecorderContext[SessionId].scope("schedule") as pool:
            with RecorderContext[SessionId].entity(session_id):
                recorder = RecorderContext[SessionId].current_recorder()
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

    def test_recorder_works_standalone_but_not_stored_in_pool(self) -> None:
        """Test that recorder can work standalone but results not stored in pool."""
        session_id = SessionId(uuid4())
        # Create recorder directly without entity context
        recorder = TransitionRecorder(session_id, datetime.now(UTC))
        with recorder.phase("validation"):
            with recorder.step("check"):
                pass

        # Recorder has phases internally
        assert len(recorder._phases) == 1
        assert recorder._phases[0].name == "validation"

        # But without entity context, nothing is stored in pool
        with RecorderContext[SessionId].scope("schedule") as pool:
            # Pool is empty since we didn't use entity context
            assert pool.get_record(session_id) is None

    def test_entity_context_nested_entities(self) -> None:
        """Test that nested entity contexts work independently."""
        session1 = SessionId(uuid4())
        session2 = SessionId(uuid4())

        with RecorderContext[SessionId].scope("schedule") as pool:
            with RecorderContext[SessionId].entity(session1):
                recorder1 = RecorderContext[SessionId].current_recorder()
                with recorder1.phase("phase1"):
                    with recorder1.step("step1"):
                        # Switch to another entity temporarily
                        with RecorderContext[SessionId].entity(session2):
                            recorder2 = RecorderContext[SessionId].current_recorder()
                            with recorder2.phase("phase2"):
                                with recorder2.step("step2"):
                                    pass

            record1 = pool.get_record(session1)
            record2 = pool.get_record(session2)

            assert record1 is not None
            assert record2 is not None
            assert record1.phases[0].name == "phase1"
            assert record2.phases[0].name == "phase2"

    def test_phase_success_detail_on_failure_is_ignored(
        self,
        session_id: SessionId,
    ) -> None:
        """Test that phase success_detail is not used when phase fails."""
        with RecorderContext[SessionId].scope("schedule") as pool:
            with RecorderContext[SessionId].entity(session_id):
                recorder = RecorderContext[SessionId].current_recorder()
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
    """Tests for shared phases functionality (using context manager API)."""

    @pytest.fixture
    def session_id(self) -> SessionId:
        return SessionId(uuid4())

    def test_shared_phase_added_to_pool(self) -> None:
        """Test that shared phases can be added to pool via context manager."""
        with RecorderContext[SessionId].scope("schedule") as pool:
            with RecorderContext[SessionId].shared_phase(
                "sequencing", success_detail="Sorted by DRF"
            ):
                with RecorderContext[SessionId].shared_step(
                    "drf", success_detail="DRF sequencing applied"
                ):
                    pass

            shared = pool.get_shared_phases()
            assert len(shared) == 1
            assert shared[0].name == "sequencing"

    def test_shared_phase_copied_to_entity_record(
        self,
        session_id: SessionId,
    ) -> None:
        """Test that shared phases are copied to entity records."""
        with RecorderContext[SessionId].scope("schedule") as pool:
            # Add shared phase before creating entities
            with RecorderContext[SessionId].shared_phase(
                "sequencing", success_detail="Sorted by DRF"
            ):
                pass

            # Create entity - should inherit shared phase
            with RecorderContext[SessionId].entity(session_id):
                recorder = RecorderContext[SessionId].current_recorder()
                with recorder.phase("validation"):
                    with recorder.step("quota_check"):
                        pass

            record = pool.get_record(session_id)
            assert record is not None
            # Should have 2 phases: sequencing (shared) + validation (entity-specific)
            assert len(record.phases) == 2
            assert record.phases[0].name == "sequencing"
            assert record.phases[1].name == "validation"

    def test_shared_phases_copied_to_multiple_entities(self) -> None:
        """Test that shared phases are copied to all entities."""
        session1 = SessionId(uuid4())
        session2 = SessionId(uuid4())

        with RecorderContext[SessionId].scope("schedule") as pool:
            # Add shared phase via context manager
            with RecorderContext[SessionId].shared_phase(
                "sequencing", success_detail="Sorted by DRF"
            ):
                pass

            # Create first entity
            with RecorderContext[SessionId].entity(session1):
                recorder = RecorderContext[SessionId].current_recorder()
                with recorder.phase("validation"):
                    with recorder.step("check1"):
                        pass

            # Create second entity
            with RecorderContext[SessionId].entity(session2):
                recorder = RecorderContext[SessionId].current_recorder()
                with recorder.phase("allocation"):
                    with recorder.step("allocate"):
                        pass

            record1 = pool.get_record(session1)
            record2 = pool.get_record(session2)

            # Both should have sequencing as first phase
            assert record1 is not None
            assert record2 is not None
            assert record1.phases[0].name == "sequencing"
            assert record2.phases[0].name == "sequencing"
            # But different second phases
            assert record1.phases[1].name == "validation"
            assert record2.phases[1].name == "allocation"

    def test_shared_phases_are_independent_copies(self) -> None:
        """Test that shared phases are independent copies for each entity."""
        session1 = SessionId(uuid4())
        session2 = SessionId(uuid4())

        with RecorderContext[SessionId].scope("schedule") as pool:
            with RecorderContext[SessionId].shared_phase("sequencing", success_detail="Sorted"):
                pass

            with RecorderContext[SessionId].entity(session1):
                pass

            with RecorderContext[SessionId].entity(session2):
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
        with RecorderContext[SessionId].scope("schedule") as pool:
            # No shared phases added
            with RecorderContext[SessionId].entity(session_id):
                recorder = RecorderContext[SessionId].current_recorder()
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
        with RecorderContext[SessionId].scope("schedule") as pool:
            with RecorderContext[SessionId].shared_phase("sequencing", success_detail="DRF"):
                pass

            # Create entity - should inherit the shared phase
            with RecorderContext[SessionId].entity(session_id):
                recorder = RecorderContext[SessionId].current_recorder()
                with recorder.phase("validation"):
                    with recorder.step("check"):
                        pass

            record = pool.get_record(session_id)
            assert record is not None
            assert len(record.phases) == 2
            assert record.phases[0].name == "sequencing"
            assert record.phases[0].status == StepStatus.SUCCESS
            assert record.phases[0].detail == "DRF"
            assert record.phases[1].name == "validation"

    def test_shared_step_within_shared_phase(
        self,
        session_id: SessionId,
    ) -> None:
        """Test shared_step() within shared_phase()."""
        with RecorderContext[SessionId].scope("schedule") as pool:
            with RecorderContext[SessionId].shared_phase("sequencing", success_detail="Sequenced"):
                with RecorderContext[SessionId].shared_step("drf", success_detail="DRF applied"):
                    pass

            with RecorderContext[SessionId].entity(session_id):
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
        with RecorderContext[SessionId].scope("schedule") as pool:
            with pytest.raises(ValueError, match="Sequencing failed"):
                with RecorderContext[SessionId].shared_phase("sequencing", success_detail="OK"):
                    raise ValueError("Sequencing failed")

            # Entity should still inherit the (failed) shared phase
            with RecorderContext[SessionId].entity(session_id):
                pass

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
        with RecorderContext[SessionId].scope("schedule") as pool:
            with pytest.raises(ValueError, match="Step failed"):
                with RecorderContext[SessionId].shared_phase("sequencing"):
                    with RecorderContext[SessionId].shared_step("drf", success_detail="OK"):
                        raise ValueError("Step failed")

            with RecorderContext[SessionId].entity(session_id):
                pass

            record = pool.get_record(session_id)
            assert record is not None
            phase = record.phases[0]
            assert phase.status == StepStatus.FAILED
            assert phase.steps[0].status == StepStatus.FAILED
            assert phase.steps[0].detail == "Step failed"

    def test_shared_step_without_phase_raises_error(self) -> None:
        """Test that shared_step() outside shared_phase() raises RuntimeError."""
        with RecorderContext[SessionId].scope("schedule"):
            with pytest.raises(RuntimeError, match="no shared phase is active"):
                with RecorderContext[SessionId].shared_step("drf"):
                    pass

    def test_nested_shared_phases_not_allowed(self) -> None:
        """Test that nested shared_phase() raises RuntimeError."""
        with RecorderContext[SessionId].scope("schedule"):
            with RecorderContext[SessionId].shared_phase("sequencing"):
                with pytest.raises(RuntimeError, match="already active"):
                    with RecorderContext[SessionId].shared_phase("sorting"):
                        pass

    def test_multiple_shared_steps_in_phase(
        self,
        session_id: SessionId,
    ) -> None:
        """Test multiple shared_step() calls within a shared_phase()."""
        with RecorderContext[SessionId].scope("schedule") as pool:
            with RecorderContext[SessionId].shared_phase("sequencing"):
                with RecorderContext[SessionId].shared_step("fifo", success_detail="FIFO"):
                    pass
                with RecorderContext[SessionId].shared_step("drf", success_detail="DRF"):
                    pass

            with RecorderContext[SessionId].entity(session_id):
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
        with RecorderContext[SessionId].scope("schedule") as pool:
            with RecorderContext[SessionId].shared_phase("sequencing"):
                with RecorderContext[SessionId].shared_step("drf"):
                    pass

            with RecorderContext[SessionId].entity(session_id):
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

        with RecorderContext[SessionId].scope("schedule") as pool:
            # Record shared phase using context manager
            with RecorderContext[SessionId].shared_phase("sequencing", success_detail="DRF"):
                with RecorderContext[SessionId].shared_step("drf"):
                    pass

            # Create first entity
            with RecorderContext[SessionId].entity(session1):
                recorder = RecorderContext[SessionId].current_recorder()
                with recorder.phase("validation"):
                    with recorder.step("check1"):
                        pass

            # Create second entity
            with RecorderContext[SessionId].entity(session2):
                recorder = RecorderContext[SessionId].current_recorder()
                with recorder.phase("allocation"):
                    with recorder.step("allocate"):
                        pass

            record1 = pool.get_record(session1)
            record2 = pool.get_record(session2)

            # Both should have sequencing as first phase
            assert record1 is not None
            assert record2 is not None
            assert record1.phases[0].name == "sequencing"
            assert record2.phases[0].name == "sequencing"
            # But different second phases
            assert record1.phases[1].name == "validation"
            assert record2.phases[1].name == "allocation"
            # Shared phases should be independent copies
            assert record1.phases[0] is not record2.phases[0]
