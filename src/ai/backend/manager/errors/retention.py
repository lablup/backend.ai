"""Retention layer exceptions."""

from __future__ import annotations

from typing import override

from ai.backend.common.exception import (
    ErrorCode,
    ErrorDetail,
    ErrorDomain,
    ErrorOperation,
)
from ai.backend.manager.errors.repository import RepositoryError


class RetentionCategoryNotSupportedError(RepositoryError):
    """Raised when a retention category has no code-side cleanup wired yet.

    The ordered-delete categories (``sessions``, ``deployments``,
    ``usage_buckets``) are implemented separately; requesting one here fails
    loudly instead of silently deleting nothing.
    """

    error_type = "https://api.backend.ai/probs/retention-category-not-supported"
    error_title = "Retention category is not supported."

    @override
    def error_code(self) -> ErrorCode:
        return ErrorCode(
            domain=ErrorDomain.BACKENDAI,
            operation=ErrorOperation.GENERIC,
            error_detail=ErrorDetail.INTERNAL_ERROR,
        )
