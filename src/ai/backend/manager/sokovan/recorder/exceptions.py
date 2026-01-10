from __future__ import annotations

from ai.backend.common.exception import (
    BackendAIError,
    ErrorCode,
    ErrorDetail,
    ErrorDomain,
    ErrorOperation,
)


class RecorderError(BackendAIError):
    """Base exception for recorder errors."""

    error_type = "https://api.backend.ai/probs/recorder-error"
    error_title = "Recorder operation failed."

    def error_code(self) -> ErrorCode:
        return ErrorCode(
            domain=ErrorDomain.SESSION,
            operation=ErrorOperation.GENERIC,
            error_detail=ErrorDetail.INTERNAL_ERROR,
        )


class NestedPhaseError(RecorderError):
    """Raised when attempting to nest phases."""

    error_type = "https://api.backend.ai/probs/nested-phase-error"
    error_title = "Nested phases are not allowed."

    def __init__(self, new_phase: str, active_phase: str) -> None:
        self.new_phase = new_phase
        self.active_phase = active_phase
        super().__init__(
            extra_msg=(
                f"Phase '{new_phase}' cannot be started: phase '{active_phase}' is already active."
            )
        )

    def error_code(self) -> ErrorCode:
        return ErrorCode(
            domain=ErrorDomain.SESSION,
            operation=ErrorOperation.GENERIC,
            error_detail=ErrorDetail.BAD_REQUEST,
        )


class StepWithoutPhaseError(RecorderError):
    """Raised when attempting to record a step without an active phase."""

    error_type = "https://api.backend.ai/probs/step-without-phase-error"
    error_title = "Step requires an active phase."

    def __init__(self, step_name: str) -> None:
        self.step_name = step_name
        super().__init__(
            extra_msg=(
                f"Step '{step_name}' cannot be recorded: no active phase. "
                "Steps must be called within a phase context."
            )
        )

    def error_code(self) -> ErrorCode:
        return ErrorCode(
            domain=ErrorDomain.SESSION,
            operation=ErrorOperation.GENERIC,
            error_detail=ErrorDetail.BAD_REQUEST,
        )
