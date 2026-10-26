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
    """Raised when a request names a value source the manager does not have."""

    error_type = "https://api.backend.ai/probs/unknown-system-session-environ-value-source"
    error_title = "The value source is not one the manager provides."

    @override
    def entity_error_code(self) -> EntityErrorCode:
        return EntityErrorCode(
            SystemSessionEnvironEntityType(), ActionOperationType.SEARCH, ErrorDetail.BAD_REQUEST
        )
