"""
Network-related exceptions.
"""

from __future__ import annotations

from typing import override

from aiohttp import web

from ai.backend.common.data.entity.network import NetworkEntityType
from ai.backend.common.exception import ErrorDetail
from ai.backend.manager.actions.types import ActionOperationType
from ai.backend.manager.errors.base.entity import EntityError, EntityErrorCode


class NetworkNotFound(EntityError, web.HTTPNotFound):
    error_type = "https://api.backend.ai/probs/network-not-found"
    error_title = "The network does not exist."

    @override
    def entity_error_code(self) -> EntityErrorCode:
        return EntityErrorCode(NetworkEntityType(), ActionOperationType.GET, ErrorDetail.NOT_FOUND)
