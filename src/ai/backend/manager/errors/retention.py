"""Retention layer exceptions."""

from __future__ import annotations

from typing import override

from aiohttp import web

from ai.backend.common.data.entity.retention_policy import RetentionPolicyEntityType
from ai.backend.common.exception import (
    ErrorCode,
    ErrorDetail,
    ErrorDomain,
    ErrorOperation,
)
from ai.backend.manager.actions.types import ActionOperationType
from ai.backend.manager.errors.base.entity import EntityError, EntityErrorCode
from ai.backend.manager.errors.repository import RepositoryError


class RetentionCategoryNotSupportedError(RepositoryError):
    """Raised when a retention category has no code-side cleanup wired.

    A defensive guard: every category the drain catalog serves is mapped, so an
    unmapped one fails loudly instead of silently deleting nothing. ``projects``
    is not in the catalog; the leader task clears it through the project
    repository.
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


class RetentionPolicyConflict(EntityError, web.HTTPConflict):
    error_type = "https://api.backend.ai/probs/duplicate-retention-policy"
    error_title = "Duplicate Retention Policy"

    @override
    def entity_error_code(self) -> EntityErrorCode:
        return EntityErrorCode(
            RetentionPolicyEntityType(), ActionOperationType.CREATE, ErrorDetail.CONFLICT
        )
