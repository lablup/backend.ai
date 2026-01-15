from __future__ import annotations

from collections.abc import Generator, Sequence
from contextlib import contextmanager
from contextvars import ContextVar
from datetime import UTC, datetime
from typing import ClassVar, Generic, Optional

from .pool import RecordPool, _SharedPhaseContext
from .types import (
    EntityIdT,
    StepRecord,
    StepStatus,
)


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
        with RecorderContext[SessionId].scope("schedule", entity_ids=session_ids) as pool:
            # Shared phase (applies to all entities)
            with RecorderContext[SessionId].shared_phase("sequencing"):
                with RecorderContext[SessionId].shared_step("drf"):
                    ...
            # Entity-specific phases
            for session_id in session_ids:
                recorder = pool.recorder(session_id)
                with recorder.phase("allocation"):
                    with recorder.step("select_agent"):
                        ...
            # Access results
            results = pool.get_all_records()
    """

    _pool_context: ClassVar[ContextVar[RecordPool]] = ContextVar("recorder_pool")  # type: ignore[type-arg]

    @classmethod
    @contextmanager
    def scope(
        cls,
        operation: str,
        entity_ids: Sequence[EntityIdT],
    ) -> Generator[RecordPool[EntityIdT], None, None]:
        """
        Create a new recorder scope.

        Args:
            operation: The operation name (e.g., "schedule", "create", "terminate").
            entity_ids: List of entity IDs to create recorders for.

        Yields:
            The RecordPool instance for accessing recorders and results.

        Usage:
            with RecorderContext[SessionId].scope("schedule", entity_ids=session_ids) as pool:
                with RecorderContext[SessionId].shared_phase("prepare"):
                    ...
                for session_id in session_ids:
                    recorder = pool.recorder(session_id)
                    with recorder.phase("work"):
                        ...
        """
        pool: RecordPool[EntityIdT] = RecordPool(
            operation=operation,
            started_at=datetime.now(UTC),
            entity_ids=entity_ids,
        )
        token = cls._pool_context.set(pool)
        try:
            yield pool
        finally:
            pool._build_all_records()
            cls._pool_context.reset(token)

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
        entity_ids: Optional[set[EntityIdT]] = None,
    ) -> Generator[None, None, None]:
        """
        Record a shared phase that applies to all or specific entities.

        Shared phases are merged with entity-specific phases when
        the scope exits, sorted by started_at timestamp.

        Args:
            name: Phase name (e.g., "sequencing")
            success_detail: Detail message on success
            entity_ids: Optional set of entity IDs to apply this phase to.
                        If None, applies to all entities in the scope.

        Raises:
            LookupError: If called outside of RecorderContext.scope()
            RuntimeError: If a shared phase is already active (nesting not allowed)

        Usage:
            with RecorderContext[SessionId].scope("op", entity_ids=ids) as pool:
                # Phase for all entities
                with RecorderContext[SessionId].shared_phase("sequencing"):
                    ...
                # Phase for specific entities only
                successful_ids = {id1, id2}
                with RecorderContext[SessionId].shared_phase("finalize", entity_ids=successful_ids):
                    ...
        """
        pool = cls._get_current_pool()

        if pool._current_shared_phase is not None:
            raise RuntimeError(
                f"Cannot start shared phase '{name}': "
                f"shared phase '{pool._current_shared_phase.name}' is already active"
            )

        phase_ctx: _SharedPhaseContext[EntityIdT] = _SharedPhaseContext(
            name=name,
            started_at=datetime.now(UTC),
            success_detail=success_detail,
            entity_ids=entity_ids,
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
