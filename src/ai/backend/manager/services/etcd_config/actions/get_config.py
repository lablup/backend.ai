from __future__ import annotations

from dataclasses import dataclass
from typing import Any, override

from ai.backend.manager.actions.action import BaseActionResult
from ai.backend.manager.actions.types import ActionOperationType

from .base import EtcdConfigAction


@dataclass
class GetConfigAction(EtcdConfigAction):
    """Action to get a raw etcd config value."""

    key: str
    prefix: bool

    @override
    @classmethod
    def operation_type(cls) -> ActionOperationType:
        return ActionOperationType.GET

    @override
    def entity_id(self) -> str | None:
        return self.key


@dataclass
class GetConfigActionResult(BaseActionResult):
    """Result of getting a config value."""

    result: Any

    @override
    def entity_id(self) -> str | None:
        return None
