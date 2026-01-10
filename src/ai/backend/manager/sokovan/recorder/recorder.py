from __future__ import annotations

from collections.abc import Generator
from contextlib import contextmanager
from dataclasses import dataclass, field
from datetime import UTC, datetime
from typing import Generic, Optional

from .exceptions import (
    NestedPhaseError,
    StepWithoutPhaseError,
)
from .types import (
    EntityIdT,
    ExecutionRecord,
    PhaseRecord,
    StepRecord,
    StepStatus,
)


@dataclass
class _PhaseContext:
    """Internal context for tracking an in-progress phase."""

    name: str
    started_at: datetime
    success_detail: Optional[str]
    steps: list[StepRecord] = field(default_factory=list)
    failed: bool = False


class TransitionRecorder(Generic[EntityIdT]):
    """
    Records execution steps during lifecycle operations.

    This class provides the API for recording phases and steps.
    It is created by RecorderContext.entity() and accumulates
    phase/step records internally until entity context exits.

    Note: Phases and steps cannot be nested. Only one phase can be
    active at a time, and only one step can be active within a phase.

    Usage:
        with RecorderContext[SessionId].scope("schedule") as pool:
            with RecorderContext[SessionId].entity(session_id):
                recorder = RecorderContext[SessionId].current_recorder()
                with recorder.phase("validation"):
                    with recorder.step("check_quota", success_detail="OK"):
                        await check_quota()
    """

    _entity_id: EntityIdT
    _started_at: datetime
    _phases: list[PhaseRecord]
    _current_phase: Optional[_PhaseContext]

    def __init__(
        self,
        entity_id: EntityIdT,
        started_at: datetime,
        initial_phases: Optional[list[PhaseRecord]] = None,
    ) -> None:
        self._entity_id = entity_id
        self._started_at = started_at
        self._phases = list(initial_phases) if initial_phases else []
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

    def build_execution_record(self, operation: str, *, failed: bool = False) -> ExecutionRecord:
        """Build the final ExecutionRecord when entity context exits.

        Args:
            operation: The operation name (e.g., "schedule", "create").
            failed: Whether the entity context exited with an exception.
        """
        return ExecutionRecord(
            operation=operation,
            started_at=self._started_at,
            ended_at=datetime.now(UTC),
            status=StepStatus.FAILED if failed else StepStatus.SUCCESS,
            phases=self._phases,
        )

    @contextmanager
    def phase(
        self,
        name: str,
        success_detail: Optional[str] = None,
    ) -> Generator[None, None, None]:
        """
        Enter a phase.

        Args:
            name: Phase name (e.g., "validation", "allocation")
            success_detail: Detail message on success

        Raises:
            NestedPhaseError: If a phase is already active (nesting not allowed)

        Usage:
            with RecorderContext[SessionId].entity(session_id):
                recorder = RecorderContext[SessionId].current_recorder()
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
        success_detail: Optional[str] = None,
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
            with RecorderContext[SessionId].entity(session_id):
                recorder = RecorderContext[SessionId].current_recorder()
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
            )
            self._current_phase.steps.append(step_record)
        except Exception as e:
            step_record = StepRecord(
                name=name,
                status=StepStatus.FAILED,
                started_at=started_at,
                ended_at=datetime.now(UTC),
                detail=str(e),
            )
            self._current_phase.steps.append(step_record)
            raise
