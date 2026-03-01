from __future__ import annotations

from dataclasses import dataclass
from typing import override

from ai.backend.manager.actions.action import BaseActionResult
from ai.backend.manager.actions.types import ActionOperationType

from .base import EtcdConfigAction


@dataclass
class DeleteConfigAction(EtcdConfigAction):
    """Action to delete a raw etcd config value."""

    key: str
    prefix: bool

    @override
    @classmethod
    def operation_type(cls) -> ActionOperationType:
        return ActionOperationType.DELETE

    @override
    def entity_id(self) -> str | None:
        return self.key


@dataclass
class DeleteConfigActionResult(BaseActionResult):
    """Result of deleting a config value."""

    @override
    def entity_id(self) -> str | None:
        return None
