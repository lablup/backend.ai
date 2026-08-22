from __future__ import annotations

from dataclasses import dataclass
from typing import Any, override

from ai.backend.common.data.entity.etcd_config import ETCD_CONFIG_ENTITY_TYPE
from ai.backend.common.data.entity.types import EntityType
from ai.backend.manager.actions.types import ActionOperationType
from ai.backend.manager.actions.v2.global_scope.base import BaseGlobalAction


@dataclass
class SetConfigAction(BaseGlobalAction):
    """Action to set a raw etcd config value."""

    key: str
    value: Any

    @override
    @classmethod
    def entity_type(cls) -> EntityType:
        return ETCD_CONFIG_ENTITY_TYPE

    @override
    @classmethod
    def operation_type(cls) -> ActionOperationType:
        return ActionOperationType.UPDATE

    @override
    @classmethod
    def action_name(cls) -> str:
        return "set_etcd_config"


@dataclass
class SetConfigActionResult:
    """Result of setting a config value."""
