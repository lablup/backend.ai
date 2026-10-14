"""Cluster-session network exceptions."""

from __future__ import annotations

from typing import override

from aiohttp import web

from ai.backend.common.data.entity.network import NetworkEntityType
from ai.backend.common.exception import (
    BackendAIError,
    ErrorCode,
    ErrorDetail,
    ErrorDomain,
    ErrorOperation,
)
from ai.backend.manager.actions.types import ActionOperationType
from ai.backend.manager.errors.base.entity import EntityNotFoundError


class NetworkNotFound(EntityNotFoundError):
    error_type = "https://api.backend.ai/probs/network-not-found"
    error_title = "The network does not exist."

    def __init__(
        self,
        extra_msg: str | None = None,
        *,
        operation: ActionOperationType = ActionOperationType.GET,
    ) -> None:
        super().__init__(extra_msg, entity_type=NetworkEntityType(), operation=operation)


class NetworkBackendMismatch(BackendAIError, web.HTTPConflict):
    """Raised when a member agent's backend cannot serve the session's network driver.

    A multi-node session cannot span nodes on different network fabrics.
    """

    error_type = "https://api.backend.ai/probs/network-backend-mismatch"
    error_title = "Agent network backend does not match the cluster network driver."

    @override
    def error_code(self) -> ErrorCode:
        return ErrorCode(
            domain=ErrorDomain.SESSION,
            operation=ErrorOperation.CREATE,
            error_detail=ErrorDetail.CONFLICT,
        )
