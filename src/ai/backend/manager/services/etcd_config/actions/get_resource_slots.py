from __future__ import annotations

from dataclasses import dataclass
from typing import Any, override

from ai.backend.manager.actions.action import BaseActionResult
from ai.backend.manager.actions.types import ActionOperationType

from .base import EtcdConfigAction


@dataclass
class GetResourceSlotsAction(EtcdConfigAction):
    """Action to get system-wide known resource slots."""

    @override
    @classmethod
    def operation_type(cls) -> ActionOperationType:
        return ActionOperationType.GET

    @override
    def entity_id(self) -> str | None:
        return None


@dataclass
class GetResourceSlotsActionResult(BaseActionResult):
    """Result of getting resource slots."""

    slots: dict[str, Any]

    @override
    def entity_id(self) -> str | None:
        return None
