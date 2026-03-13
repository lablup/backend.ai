from __future__ import annotations

from dataclasses import dataclass
from typing import override

from ai.backend.manager.actions.action import BaseActionResult
from ai.backend.manager.actions.types import ActionOperationType

from .base import ManagerAdminAction


@dataclass
class FetchManagerStatusAction(ManagerAdminAction):
    """Action to fetch the current manager status."""

    @override
    @classmethod
    def operation_type(cls) -> ActionOperationType:
        return ActionOperationType.GET

    @override
    def entity_id(self) -> str | None:
        return None


@dataclass
class FetchManagerStatusActionResult(BaseActionResult):
    """Result of fetching manager status."""

    status: str
    active_sessions: int
    manager_id: str
    num_proc: int
    service_addr: str
    heartbeat_timeout: float
    ssl_enabled: bool

    @override
    def entity_id(self) -> str | None:
        return None
