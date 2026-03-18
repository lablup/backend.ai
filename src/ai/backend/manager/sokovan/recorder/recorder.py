from __future__ import annotations

from collections.abc import Generator
from contextlib import contextmanager
from dataclasses import dataclass, field
from datetime import UTC, datetime
from uuid import UUID

from ai.backend.common.exception import BackendAIError

from .exceptions import (
    NestedPhaseError,
    StepWithoutPhaseError,
)
from .types import (
    ExecutionRecord,
    PhaseRecord,
    RecordBuildData,
    StepRecord,
    StepStatus,
)


@dataclass
class _PhaseContext:
    """Internal context for tracking an in-progress phase."""

    name: str
    started_at: datetime
    success_detail: str | None
    steps: list[StepRecord] = field(default_factory=list)
    failed: bool = False


class TransitionRecorder[EntityIdT: UUID]:
    """
    Records execution steps during lifecycle operations.

    This class provides the API for recording phases and steps.
    It is created by RecordPool when scope() is entered and accumulates
    phase/step records internally until scope exits.

    Note: Phases and steps cannot be nested. Only one phase can be
    active at a time, and only one step can be active within a phase.

    Usage:
        with RecorderContext[SessionId].scope("schedule", entity_ids=session_ids) as pool:
            recorder = pool.recorder(session_id)
            with recorder.phase("validation"):
                with recorder.step("check_quota", success_detail="OK"):
                    await check_quota()
    """

    _entity_id: EntityIdT
    _started_at: datetime
    _phases: list[PhaseRecord]
    _current_phase: _PhaseContext | None

    def __init__(
        self,
        entity_id: EntityIdT,
        started_at: datetime,
    ) -> None:
        self._entity_id = entity_id
        self._started_at = started_at
        self._phases = []
        self._current_phase = None

    @property
    def entity_id(self) -> EntityIdT:
        """Get the entity ID for this recorder."""
        return self._entity_id

    def _finalize_phase(self, phase_ctx: _PhaseContext) -> None:
        """Finalize and record a completed phase."""
        ended_at = datetime.now(UTC)

        if phase_ctx.failed:
            status = StepStatus.FAILED
            detail = None
        else:
            status = StepStatus.SUCCESS
            detail = phase_ctx.success_detail

        phase_record = PhaseRecord(
            name=phase_ctx.name,
            status=status,
            started_at=phase_ctx.started_at,
            ended_at=ended_at,
            detail=detail,
            steps=phase_ctx.steps,
        )
        self._phases.append(phase_record)

    def build_execution_record(self, build_data: RecordBuildData) -> ExecutionRecord:
        """Build the final ExecutionRecord when scope exits.

        Args:
            build_data: Data containing shared phases for this entity.
        """
        # Merge shared phases (copied) with entity phases
        all_phases = [p.model_copy(deep=True) for p in build_data.shared_phases]
        all_phases.extend(self._phases)

        # Sort by started_at to maintain execution order
        all_phases.sort(key=lambda p: p.started_at)

        return ExecutionRecord(
            started_at=build_data.started_at,
            ended_at=build_data.ended_at,
            phases=all_phases,
        )

    @contextmanager
    def phase(
        self,
        name: str,
        success_detail: str | None = None,
    ) -> Generator[None, None, None]:
        """
        Enter a phase.

        Args:
            name: Phase name (e.g., "validation", "allocation")
            success_detail: Detail message on success

        Raises:
            NestedPhaseError: If a phase is already active (nesting not allowed)

        Usage:
            with RecorderContext[SessionId].scope("op", entity_ids=ids) as pool:
                recorder = pool.recorder(session_id)
                with recorder.phase("validation", success_detail="All passed"):
                    pass
        """
        if self._current_phase is not None:
            raise NestedPhaseError(name, self._current_phase.name)

        phase_ctx = _PhaseContext(
            name=name,
            started_at=datetime.now(UTC),
            success_detail=success_detail,
        )
        self._current_phase = phase_ctx

        try:
            yield
        except Exception:
            phase_ctx.failed = True
            raise
        finally:
            self._current_phase = None
            self._finalize_phase(phase_ctx)

    @contextmanager
    def step(
        self,
        name: str,
        success_detail: str | None = None,
    ) -> Generator[None, None, None]:
        """
        Execute a step with automatic success/failure recording.

        Must be called within a phase context.

        Args:
            name: Step name (e.g., "check_quota", "select_agent")
            success_detail: Detail message on success

        Raises:
            StepWithoutPhaseError: If no phase is active

        Usage:
            with RecorderContext[SessionId].scope("op", entity_ids=ids) as pool:
                recorder = pool.recorder(session_id)
                with recorder.phase("validation"):
                    with recorder.step("check_quota", success_detail="Quota OK"):
                        await check_quota()
        """
        if self._current_phase is None:
            raise StepWithoutPhaseError(name)

        started_at = datetime.now(UTC)

        try:
            yield
            step_record = StepRecord(
                name=name,
                status=StepStatus.SUCCESS,
                started_at=started_at,
                ended_at=datetime.now(UTC),
                detail=success_detail,
                error_code=None,
            )
            self._current_phase.steps.append(step_record)
        except Exception as e:
            error_code = str(e.error_code()) if isinstance(e, BackendAIError) else None
            step_record = StepRecord(
                name=name,
                status=StepStatus.FAILED,
                started_at=started_at,
                ended_at=datetime.now(UTC),
                detail=str(e),
                error_code=error_code,
            )
            self._current_phase.steps.append(step_record)
            raise
