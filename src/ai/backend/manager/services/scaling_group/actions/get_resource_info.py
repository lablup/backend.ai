from __future__ import annotations

from dataclasses import dataclass
from typing import override

from ai.backend.manager.actions.action import BaseActionResult
from ai.backend.manager.data.scaling_group.types import ResourceInfo

from .base import ScalingGroupAction


@dataclass
class GetResourceInfoAction(ScalingGroupAction):
    """Action to get resource information for a scaling group."""

    scaling_group: str

    @override
    @classmethod
    def operation_type(cls) -> str:
        return "get_resource_info"

    @override
    def entity_id(self) -> str:
        return self.scaling_group


@dataclass
class GetResourceInfoActionResult(BaseActionResult):
    """Result of getting resource information."""

    resource_info: ResourceInfo

    @override
    def entity_id(self) -> str | None:
        return None
