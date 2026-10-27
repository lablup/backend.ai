"""
System session environ domain exceptions.
"""

from __future__ import annotations

from typing import override

from aiohttp import web

from ai.backend.common.data.entity.system_session_environ import SystemSessionEnvironEntityType
from ai.backend.common.exception import ErrorDetail
from ai.backend.manager.actions.types import ActionOperationType
from ai.backend.manager.errors.base.entity import EntityError, EntityErrorCode


class UnknownSystemSessionEnvironValueSource(EntityError, web.HTTPBadRequest):
    error_type = "https://api.backend.ai/probs/unknown-system-session-environ-value-source"
    error_title = "The value source is not one the manager provides."

    @override
    def entity_error_code(self) -> EntityErrorCode:
        return EntityErrorCode(
            SystemSessionEnvironEntityType(), ActionOperationType.SEARCH, ErrorDetail.BAD_REQUEST
        )


class SystemSessionEnvironKeyConflict(EntityError, web.HTTPConflict):
    """Raised when another row at the same scope already holds the key."""

    error_type = "https://api.backend.ai/probs/system-session-environ-key-conflict"
    error_title = "Another system session environ row at the same scope already holds the key."

    @override
    def entity_error_code(self) -> EntityErrorCode:
        return EntityErrorCode(
            SystemSessionEnvironEntityType(), ActionOperationType.UPDATE, ErrorDetail.CONFLICT
        )


class InvalidSystemSessionEnvironKey(EntityError, web.HTTPBadRequest):
    """Raised when the key is not an environment variable name."""

    error_type = "https://api.backend.ai/probs/invalid-system-session-environ-key"
    error_title = "The key must be an environment variable name."

    @override
    def entity_error_code(self) -> EntityErrorCode:
        return EntityErrorCode(
            SystemSessionEnvironEntityType(), ActionOperationType.UPDATE, ErrorDetail.BAD_REQUEST
        )
