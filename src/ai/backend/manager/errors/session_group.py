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


class InvalidSessionGroupAdmission(EntityError, web.HTTPBadRequest):
    """Raised when a session group's member count does not match its admission: an
    `all_or_none` group needs at least two members, an `independent` group none."""

    error_type = "https://api.backend.ai/probs/invalid-session-group-admission"
    error_title = "The member count does not match the session group's admission."

    @override
    def entity_error_code(self) -> EntityErrorCode:
        return EntityErrorCode(
            SessionGroupEntityType(), ActionOperationType.UPDATE, ErrorDetail.INVALID_PARAMETERS
        )


class SessionGroupAdmissionInUse(EntityError, web.HTTPConflict):
    """Raised when changing the admission or the member count of a session group whose
    members are pending."""

    error_type = "https://api.backend.ai/probs/session-group-admission-in-use"
    error_title = "The admission of a session group cannot change while its members are pending."

    @override
    def entity_error_code(self) -> EntityErrorCode:
        return EntityErrorCode(
            SessionGroupEntityType(), ActionOperationType.UPDATE, ErrorDetail.CONFLICT
        )


class SessionGroupFull(EntityError, web.HTTPConflict):
    """Raised when a session joins an `all_or_none` group that already holds its member count."""

    error_type = "https://api.backend.ai/probs/session-group-full"
    error_title = "The session group already holds its member count."

    @override
    def entity_error_code(self) -> EntityErrorCode:
        return EntityErrorCode(
            SessionEntityType(), ActionOperationType.CREATE, ErrorDetail.CONFLICT
        )


class SessionGroupResourceGroupMismatch(EntityError, web.HTTPConflict):
    """Raised when a session joins an `all_or_none` group whose members run in another
    resource group."""

    error_type = "https://api.backend.ai/probs/session-group-resource-group-mismatch"
    error_title = "Every member of an all-or-none session group belongs to one resource group."

    @override
    def entity_error_code(self) -> EntityErrorCode:
        return EntityErrorCode(
            SessionEntityType(), ActionOperationType.CREATE, ErrorDetail.CONFLICT
        )
