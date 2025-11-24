from __future__ import annotations

from collections import defaultdict
from contextlib import contextmanager
from datetime import datetime, timezone
from typing import Generator

from ai.backend.common.types import SessionId

from .types import ExecutionStep, PhaseDescriptor, StepDescriptor


class TransitionRecorder:
    """
    Records execution steps during scheduler lifecycle operations.

    Supports hierarchical phases and automatic success/failure recording via context managers.
    """

    def __init__(self, operation: str) -> None:
        self._operation = operation
        self._steps: dict[SessionId, list[ExecutionStep]] = defaultdict(list)
        self._phase_stack: dict[SessionId, list[str]] = defaultdict(list)

    @property
    def operation(self) -> str:
        """Get the operation name for this recorder."""
        return self._operation

    @contextmanager
    def phase(self, desc: PhaseDescriptor) -> Generator[None, None, None]:
        """
        Enter a phase (hierarchical grouping).

        Usage:
            with recorder.phase(PhaseDescriptor(session_id, "provisioner")):
                with recorder.phase(PhaseDescriptor(session_id, "validator")):
                    # steps here will have phase ["provisioner", "validator"]
        """
        self._phase_stack[desc.session_id].append(desc.name)
        try:
            yield
        finally:
            self._phase_stack[desc.session_id].pop()

    @contextmanager
    def step(self, desc: StepDescriptor) -> Generator[None, None, None]:
        """
        Execute a step with automatic success/failure recording.

        Records "started" on entry, "success" on normal exit, "failed" on exception.

        Usage:
            with recorder.step(StepDescriptor(session_id, "check_quota", "Quota validated")):
                await check_quota()
                # On success: records "success" with success_detail
                # On exception: records "failed" with exception message
        """
        phases = self._get_current_phases(desc.session_id)
        self._record(desc.session_id, phases, desc.name, "started", None)
        try:
            yield
            self._record(desc.session_id, phases, desc.name, "success", desc.success_detail)
        except Exception as e:
            self._record(desc.session_id, phases, desc.name, "failed", str(e))
            raise

    def _get_current_phases(self, session_id: SessionId) -> list[str]:
        """Get the current phase stack for a session."""
        return list(self._phase_stack[session_id])

    def _record(
        self,
        session_id: SessionId,
        phases: list[str],
        name: str,
        status: str,
        detail: str | None,
    ) -> None:
        """Internal method to record an execution step."""
        self._steps[session_id].append(
            ExecutionStep(
                phases=phases,
                name=name,
                status=status,
                timestamp=datetime.now(timezone.utc),
                detail=detail,
            )
        )

    def get_steps(self, session_id: SessionId) -> list[ExecutionStep]:
        """Get all recorded steps for a specific session."""
        return list(self._steps[session_id])

    def get_all_steps(self) -> dict[SessionId, list[ExecutionStep]]:
        """Get all recorded steps for all sessions."""
        return dict(self._steps)
