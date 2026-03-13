from __future__ import annotations

from dataclasses import dataclass, field
from typing import override

from ai.backend.manager.actions.action import BaseActionResult
from ai.backend.manager.actions.types import ActionOperationType
from ai.backend.manager.models.health import ConnectionInfoOfProcess

from .base import ManagerAdminAction


@dataclass
class GetDbCxnStatusAction(ManagerAdminAction):
    """Action to get database connection status for Prometheus metrics."""

    @override
    @classmethod
    def operation_type(cls) -> ActionOperationType:
        return ActionOperationType.GET

    @override
    def entity_id(self) -> str | None:
        return None


@dataclass
class GetDbCxnStatusActionResult(BaseActionResult):
    """Result containing database connection status info."""

    cxn_infos: list[ConnectionInfoOfProcess] = field(default_factory=list)

    @override
    def entity_id(self) -> str | None:
        return None
