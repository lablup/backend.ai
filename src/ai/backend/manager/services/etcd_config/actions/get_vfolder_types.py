from __future__ import annotations

from dataclasses import dataclass
from typing import override

from ai.backend.manager.actions.action import BaseActionResult
from ai.backend.manager.actions.types import ActionOperationType

from .base import EtcdConfigAction


@dataclass
class GetVfolderTypesAction(EtcdConfigAction):
    """Action to get available vfolder types."""

    @override
    @classmethod
    def operation_type(cls) -> ActionOperationType:
        return ActionOperationType.GET

    @override
    def entity_id(self) -> str | None:
        return None


@dataclass
class GetVfolderTypesActionResult(BaseActionResult):
    """Result of getting vfolder types."""

    types: list[str]

    @override
    def entity_id(self) -> str | None:
        return None
