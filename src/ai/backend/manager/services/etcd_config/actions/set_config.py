from __future__ import annotations

from dataclasses import dataclass
from typing import Any, override

from ai.backend.manager.actions.action import BaseActionResult
from ai.backend.manager.actions.types import ActionOperationType

from .base import EtcdConfigAction


@dataclass
class SetConfigAction(EtcdConfigAction):
    """Action to set a raw etcd config value."""

    key: str
    value: Any

    @override
    @classmethod
    def operation_type(cls) -> ActionOperationType:
        return ActionOperationType.UPDATE

    @override
    def entity_id(self) -> str | None:
        return self.key


@dataclass
class SetConfigActionResult(BaseActionResult):
    """Result of setting a config value."""

    @override
    def entity_id(self) -> str | None:
        return None
