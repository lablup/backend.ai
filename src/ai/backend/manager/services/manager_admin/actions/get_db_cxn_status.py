from __future__ import annotations

from dataclasses import dataclass, field
from typing import override

from ai.backend.common.data.entity.manager_admin import MANAGER_ADMIN_ENTITY_TYPE
from ai.backend.common.data.entity.types import EntityType
from ai.backend.manager.actions.types import ActionOperationType
from ai.backend.manager.actions.v2.global_scope.base import BaseGlobalAction
from ai.backend.manager.repositories.manager_admin.health import ConnectionInfoOfProcess


@dataclass
class GetDbCxnStatusAction(BaseGlobalAction):
    """Action to get database connection status for Prometheus metrics."""

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
        return "get_db_connection_status"


@dataclass
class GetDbCxnStatusActionResult:
    """Result containing database connection status info."""

    cxn_infos: list[ConnectionInfoOfProcess] = field(default_factory=list)
