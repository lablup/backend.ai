"""Retention layer exceptions."""

from __future__ import annotations

from typing import override

from aiohttp import web

from ai.backend.common.exception import (
    BackendAIError,
    ErrorCode,
    ErrorDetail,
    ErrorDomain,
    ErrorOperation,
)
from ai.backend.manager.errors.repository import RepositoryError

from .common import ObjectNotFound


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


class RetentionPolicyNotFound(ObjectNotFound):
    object_name = "retention policy"

    @override
    def error_code(self) -> ErrorCode:
        return ErrorCode(
            domain=ErrorDomain.RETENTION_POLICY,
            operation=ErrorOperation.READ,
            error_detail=ErrorDetail.NOT_FOUND,
        )


class RetentionPolicyConflict(BackendAIError, web.HTTPConflict):
    error_type = "https://api.backend.ai/probs/duplicate-retention-policy"
    error_title = "Duplicate Retention Policy"

    @override
    def error_code(self) -> ErrorCode:
        return ErrorCode(
            domain=ErrorDomain.RETENTION_POLICY,
            operation=ErrorOperation.GENERIC,
            error_detail=ErrorDetail.CONFLICT,
        )
