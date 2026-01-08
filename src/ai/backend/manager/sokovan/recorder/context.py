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
)


@dataclass
class RecordPool(Generic[EntityIdT]):
    """Storage for all entity execution records within a scope.

    This class holds the operation metadata and all recorded execution
    results for entities processed within a RecorderContext scope.
    Records are only added when entity context exits (finalized).
    """

    operation: str
    started_at: datetime
    records: dict[EntityIdT, ExecutionRecord] = field(default_factory=dict)

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
    def _get_current_pool(cls) -> RecordPool[EntityIdT]:
        """
        Get the current RecordPool (internal use).

        Returns:
            The RecordPool instance for the current scope.

        Raises:
            LookupError: If called outside of a RecorderContext.scope().
        """
        return cls._pool_context.get()
