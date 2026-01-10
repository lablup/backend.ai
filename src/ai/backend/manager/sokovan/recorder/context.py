from __future__ import annotations

from collections.abc import Generator
from contextlib import contextmanager
from contextvars import ContextVar
from dataclasses import dataclass, field
from datetime import UTC, datetime
from typing import ClassVar, Generic, Optional

from .recorder import TransitionRecorder
from .types import (
    EntityIdT,
    ExecutionRecord,
    PhaseRecord,
    StepRecord,
    StepStatus,
)


@dataclass
class _SharedPhaseContext:
    """Internal context for tracking an in-progress shared phase."""

    name: str
    started_at: datetime
    success_detail: Optional[str]
    steps: list[StepRecord] = field(default_factory=list)
    failed: bool = False


@dataclass
class RecordPool(Generic[EntityIdT]):
    """Storage for all entity execution records within a scope.

    This class holds the operation metadata and all recorded execution
    results for entities processed within a RecorderContext scope.
    Records are only added when entity context exits (finalized).

    Supports shared phases that are copied to all entity recorders
    when they are created (e.g., sequencing phase that applies to all sessions).
    """

    operation: str
    started_at: datetime
    records: dict[EntityIdT, ExecutionRecord] = field(default_factory=dict)
    _shared_phases: list[PhaseRecord] = field(default_factory=list)
    _current_shared_phase: Optional[_SharedPhaseContext] = field(default=None)

    def _finalize_shared_phase(self, phase_ctx: _SharedPhaseContext) -> None:
        """Finalize and record a completed shared phase."""
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
        self._shared_phases.append(phase_record)

    def get_shared_phases(self) -> list[PhaseRecord]:
        """Get a copy of all shared phases.

        Returns a deep copy so each entity gets independent phase records.
        """
        return [phase.model_copy(deep=True) for phase in self._shared_phases]

    def get_record(self, entity_id: EntityIdT) -> Optional[ExecutionRecord]:
        """Get the execution record for an entity."""
        return self.records.get(entity_id)

    def get_all_records(self) -> dict[EntityIdT, ExecutionRecord]:
        """Get all execution records."""
        return dict(self.records)


class RecorderContext(Generic[EntityIdT]):
    """
    Manages the recording scope via ContextVar for coordinator operations.

    Generic over the entity ID type to support different coordinator contexts:
    - SessionId for scheduler coordinator
    - UUID for deployment/route coordinators

    Provides a scoped context for recording execution steps without
    explicitly passing the recorder through all function calls.

    Usage:
        # At coordinator entry point
        with RecorderContext[SessionId].scope("schedule") as pool:
            with RecorderContext[SessionId].entity(session_id):
                recorder = RecorderContext[SessionId].current_recorder()
                with recorder.phase("validation"):
                    with recorder.step("check_quota"):
                        ...
            # Access results
            results = pool.get_all_records()
    """

    _pool_context: ClassVar[ContextVar[RecordPool]] = ContextVar("recorder_pool")  # type: ignore[type-arg]
    _recorder_context: ClassVar[ContextVar[TransitionRecorder]] = ContextVar("current_recorder")  # type: ignore[type-arg]

    @classmethod
    @contextmanager
    def scope(cls, operation: str) -> Generator[RecordPool[EntityIdT], None, None]:
        """
        Create a new recorder scope.

        Args:
            operation: The operation name (e.g., "schedule", "create", "terminate").

        Yields:
            The RecordPool instance for accessing results after recording.
        """
        pool: RecordPool[EntityIdT] = RecordPool(
            operation=operation,
            started_at=datetime.now(UTC),
        )
        token = cls._pool_context.set(pool)
        try:
            yield pool
        finally:
            cls._pool_context.reset(token)

    @classmethod
    @contextmanager
    def entity(cls, entity_id: EntityIdT) -> Generator[None, None, None]:
        """
        Enter an entity context and create a recorder for it.

        Args:
            entity_id: The entity ID to record for.

        Yields:
            None. Use current_recorder() to get the recorder.
        """
        pool = cls._get_current_pool()
        recorder: TransitionRecorder[EntityIdT] = TransitionRecorder(
            entity_id=entity_id,
            started_at=datetime.now(UTC),
            initial_phases=pool.get_shared_phases(),
        )
        token = cls._recorder_context.set(recorder)
        failed = False
        try:
            yield
        except Exception:
            failed = True
            raise
        finally:
            cls._recorder_context.reset(token)
            # Finalize: build ExecutionRecord and store in pool
            pool.records[entity_id] = recorder.build_execution_record(pool.operation, failed=failed)

    @classmethod
    def current_recorder(cls) -> TransitionRecorder[EntityIdT]:
        """
        Get the TransitionRecorder for the current entity.

        Returns:
            The TransitionRecorder instance for the current entity context.

        Raises:
            LookupError: If called outside of a RecorderContext.entity().
        """
        return cls._recorder_context.get()

    @classmethod
    def current_pool(cls) -> RecordPool[EntityIdT]:
        """
        Get the current RecordPool.

        Returns:
            The RecordPool instance for the current scope.

        Raises:
            LookupError: If called outside of a RecorderContext.scope().
        """
        return cls._pool_context.get()

    @classmethod
    def _get_current_pool(cls) -> RecordPool[EntityIdT]:
        """
        Get the current RecordPool (internal use).

        Returns:
            The RecordPool instance for the current scope.

        Raises:
            LookupError: If called outside of a RecorderContext.scope().
        """
        return cls._pool_context.get()

    @classmethod
    @contextmanager
    def shared_phase(
        cls,
        name: str,
        success_detail: Optional[str] = None,
    ) -> Generator[None, None, None]:
        """
        Record a shared phase that applies to all entities.

        Shared phases are automatically copied to each entity's recorder
        when entity() is called. Use this for batch-level operations
        (e.g., sequencing) that apply to all entities in the batch.

        Args:
            name: Phase name (e.g., "sequencing")
            success_detail: Detail message on success

        Raises:
            LookupError: If called outside of RecorderContext.scope()
            RuntimeError: If a shared phase is already active (nesting not allowed)

        Usage:
            with RecorderContext[SessionId].scope("provisioning"):
                with RecorderContext[SessionId].shared_phase("sequencing", success_detail="DRF"):
                    with RecorderContext[SessionId].shared_step("drf", success_detail="Sequenced"):
                        sequenced = sequencer.sequence(...)
                # Now entity() calls will include the sequencing phase
                for session_id in sessions:
                    with RecorderContext[SessionId].entity(session_id):
                        ...
        """
        pool = cls._get_current_pool()

        if pool._current_shared_phase is not None:
            raise RuntimeError(
                f"Cannot start shared phase '{name}': "
                f"shared phase '{pool._current_shared_phase.name}' is already active"
            )

        phase_ctx = _SharedPhaseContext(
            name=name,
            started_at=datetime.now(UTC),
            success_detail=success_detail,
        )
        pool._current_shared_phase = phase_ctx

        try:
            yield
        except Exception:
            phase_ctx.failed = True
            raise
        finally:
            pool._current_shared_phase = None
            pool._finalize_shared_phase(phase_ctx)

    @classmethod
    @contextmanager
    def shared_step(
        cls,
        name: str,
        success_detail: Optional[str] = None,
    ) -> Generator[None, None, None]:
        """
        Record a step within a shared phase.

        Must be called within a shared_phase() context.

        Args:
            name: Step name (e.g., "drf", "fifo")
            success_detail: Detail message on success

        Raises:
            LookupError: If called outside of RecorderContext.scope()
            RuntimeError: If no shared phase is active

        Usage:
            with RecorderContext[SessionId].shared_phase("sequencing"):
                with RecorderContext[SessionId].shared_step("drf", success_detail="Sequenced"):
                    sequenced = sequencer.sequence(...)
        """
        pool = cls._get_current_pool()

        if pool._current_shared_phase is None:
            raise RuntimeError(f"Cannot start shared step '{name}': no shared phase is active")

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
            pool._current_shared_phase.steps.append(step_record)
        except Exception as e:
            step_record = StepRecord(
                name=name,
                status=StepStatus.FAILED,
                started_at=started_at,
                ended_at=datetime.now(UTC),
                detail=str(e),
            )
            pool._current_shared_phase.steps.append(step_record)
            raise
