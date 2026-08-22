from __future__ import annotations

from dataclasses import dataclass
from typing import override

from ai.backend.common.data.entity.manager_admin import MANAGER_ADMIN_ENTITY_TYPE
from ai.backend.common.data.entity.types import EntityType
from ai.backend.manager.actions.types import ActionOperationType
from ai.backend.manager.actions.v2.global_scope.base import BaseGlobalAction


@dataclass
class FetchManagerStatusAction(BaseGlobalAction):
    """Action to fetch the current manager status."""

    @override
    @classmethod
    def entity_type(cls) -> EntityType:
        return MANAGER_ADMIN_ENTITY_TYPE

    @override
    @classmethod
    def operation_type(cls) -> ActionOperationType:
        return ActionOperationType.GET

    @override
    @classmethod
    def action_name(cls) -> str:
        return "fetch_manager_status"


@dataclass
class FetchManagerStatusActionResult:
    """Result of fetching manager status."""

    status: str
    active_sessions: int
    manager_id: str
    num_proc: int
    service_addr: str
    heartbeat_timeout: float
    ssl_enabled: bool
