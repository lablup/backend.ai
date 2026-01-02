from __future__ import annotations

from contextlib import contextmanager
from contextvars import ContextVar
from typing import ClassVar, Generator

from .recorder import TransitionRecorder


class RecorderContext:
    """
    Manages the TransitionRecorder via ContextVar for scheduler scope.

    Provides a scoped context for recording execution steps without
    explicitly passing the recorder through all function calls.

    Usage:
        # At coordinator entry point
        with RecorderContext.scope() as recorder:
            result = await handler.execute(sessions)
            await save_history(recorder.get_all_steps())

        # Anywhere nested within the scope
        RecorderContext.current().step(StepDescriptor(...))
    """

    _context: ClassVar[ContextVar[TransitionRecorder]] = ContextVar("scheduler_recorder")

    @classmethod
    @contextmanager
    def scope(cls, operation: str) -> Generator[TransitionRecorder, None, None]:
        """
        Create a new recorder scope.

        Args:
            operation: The operation name (e.g., "schedule", "create", "terminate").

        Returns:
            The TransitionRecorder instance for this scope.
        """
        recorder = TransitionRecorder(operation)
        token = cls._context.set(recorder)
        try:
            yield recorder
        finally:
            cls._context.reset(token)

    @classmethod
    def current(cls) -> TransitionRecorder:
        """
        Get the current TransitionRecorder from the context.

        Returns:
            The active TransitionRecorder instance.

        Raises:
            LookupError: If called outside of a RecorderContext.scope().
        """
        return cls._context.get()
