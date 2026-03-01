from __future__ import annotations

from dataclasses import dataclass
from typing import override

from ai.backend.common.types import AcceleratorMetadata
from ai.backend.manager.actions.action import BaseActionResult
from ai.backend.manager.actions.types import ActionOperationType

from .base import EtcdConfigAction


@dataclass
class GetResourceMetadataAction(EtcdConfigAction):
    """Action to get resource metadata with optional scaling group filter."""

    sgroup: str | None

    @override
    @classmethod
    def operation_type(cls) -> ActionOperationType:
        return ActionOperationType.GET

    @override
    def entity_id(self) -> str | None:
        return self.sgroup


@dataclass
class GetResourceMetadataActionResult(BaseActionResult):
    """Result of getting resource metadata."""

    metadata: dict[str, AcceleratorMetadata]

    @override
    def entity_id(self) -> str | None:
        return None
