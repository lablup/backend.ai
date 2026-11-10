"""
Network-related exceptions.
"""

from __future__ import annotations

from ai.backend.common.data.entity.network import NetworkEntityType
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
