"""
Session group domain exceptions.
"""

from __future__ import annotations

from typing import override

from aiohttp import web

from ai.backend.common.data.entity.session import SessionEntityType
from ai.backend.common.data.entity.session_group import SessionGroupEntityType
from ai.backend.common.exception import ErrorDetail
from ai.backend.manager.actions.types import ActionOperationType
from ai.backend.manager.errors.base.entity import (
    EntityError,
    EntityErrorCode,
    EntityNotFoundError,
)


class SessionGroupNotFound(EntityNotFoundError):
    """Raised when an operation names a session group that does not exist or that the
    caller may not use."""

    error_type = "https://api.backend.ai/probs/session-group-not-found"
    error_title = "The session group does not exist."

    def __init__(
        self,
        extra_msg: str | None = None,
        *,
        operation: ActionOperationType = ActionOperationType.GET,
    ) -> None:
        super().__init__(extra_msg, entity_type=SessionGroupEntityType(), operation=operation)


class SessionGroupInUse(EntityError, web.HTTPConflict):
    """Raised when purging a session group a deployment's replica group still references."""

    error_type = "https://api.backend.ai/probs/session-group-in-use"
    error_title = "Session group cannot be purged while a replica group uses it."

    @override
    def entity_error_code(self) -> EntityErrorCode:
        return EntityErrorCode(
            SessionGroupEntityType(), ActionOperationType.PURGE, ErrorDetail.CONFLICT
        )


class SessionGroupInUseForUpdate(EntityError, web.HTTPConflict):
    """Raised when updating a session group a deployment's replica group still references."""

    error_type = "https://api.backend.ai/probs/session-group-in-use"
    error_title = "Session group cannot be updated while a replica group uses it."

    @override
    def entity_error_code(self) -> EntityErrorCode:
        return EntityErrorCode(
            SessionGroupEntityType(), ActionOperationType.UPDATE, ErrorDetail.CONFLICT
        )


class SessionGroupInUseForEnqueue(EntityError, web.HTTPConflict):
    """Raised when enqueuing a session into a session group a deployment's replica group references."""

    error_type = "https://api.backend.ai/probs/session-group-in-use"
    error_title = "A session cannot join a session group a replica group uses."

    @override
    def entity_error_code(self) -> EntityErrorCode:
        return EntityErrorCode(
            SessionEntityType(), ActionOperationType.CREATE, ErrorDetail.CONFLICT
        )
