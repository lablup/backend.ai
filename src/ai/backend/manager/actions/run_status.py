import logging
from dataclasses import dataclass
from typing import Self

from ai.backend.common.exception import BackendAIError, ErrorCode, ErrorDetail
from ai.backend.logging.utils import BraceStyleAdapter

from .types import OperationStatus

__all__ = ("ActionRunStatus",)

log = BraceStyleAdapter(logging.getLogger(__spec__.name))


@dataclass(frozen=True)
class ActionRunStatus:
    """The audit-visible fields of an action run's end state."""

    status: OperationStatus
    description: str
    error_code: ErrorCode | None

    @classmethod
    def unknown(cls) -> Self:
        return cls(status=OperationStatus.UNKNOWN, description="unknown", error_code=None)

    @classmethod
    def success(cls) -> Self:
        return cls(status=OperationStatus.SUCCESS, description="Success", error_code=None)

    @classmethod
    def of_failure(cls, exc: BaseException, *, during_validation: bool) -> Self:
        """Classify a raised exception.

        A validator rejecting the action gives DENIED rather than ERROR: a denial is
        the signal an audit trail exists for, and must be distinguishable from the
        action itself going wrong. Anything else that fails while validating — a
        permission lookup timing out, say — is an ordinary ERROR.
        """
        if isinstance(exc, BackendAIError):
            log.exception("Action processing error: {}", exc)
            error_code = exc.error_code()
            denied = during_validation and error_code.error_detail == ErrorDetail.FORBIDDEN
            return cls(
                status=OperationStatus.DENIED if denied else OperationStatus.ERROR,
                description=str(exc),
                error_code=error_code,
            )
        log.exception("Unexpected error during action processing: {}", exc)
        return cls(
            status=OperationStatus.ERROR,
            description=str(exc),
            error_code=ErrorCode.default(),
        )
