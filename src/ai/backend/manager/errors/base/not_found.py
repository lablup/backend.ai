"""Shared root of the errors reporting that a named row does not exist."""

from __future__ import annotations

from ai.backend.common.exception import BackendAIError


class NotFoundError(BackendAIError):
    """Raised when an operation names a row that does not exist.

    Declares nothing of its own, so it still owes the error code and cannot be
    constructed. It exists to be caught: a caller that answers the same way for a
    missing entity and a missing field row names this instead of both.
    """
