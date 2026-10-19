"""
Session group domain exceptions.
"""

from __future__ import annotations

from typing import override

from aiohttp import web

from ai.backend.common.data.entity.session_group import SessionGroupEntityType
from ai.backend.common.exception import ErrorDetail
from ai.backend.manager.actions.types import ActionOperationType
from ai.backend.manager.errors.base.entity import EntityError, EntityErrorCode


class SessionGroupInUse(EntityError, web.HTTPConflict):
    """Raised when purging a session group a deployment's replica group still references."""

    error_type = "https://api.backend.ai/probs/session-group-in-use"
    error_title = "Session group cannot be purged while a replica group uses it."

    @override
    def entity_error_code(self) -> EntityErrorCode:
        return EntityErrorCode(
            SessionGroupEntityType(), ActionOperationType.PURGE, ErrorDetail.CONFLICT
        )
