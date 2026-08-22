from __future__ import annotations

from dataclasses import dataclass
from typing import override

from ai.backend.manager.actions.types import ActionOperationType
from ai.backend.manager.data.resource_group.types import ResourceInfo

from .base import ResourceGroupAction


@dataclass(frozen=True)
class GetResourceInfoAction(ResourceGroupAction):
    """Action to get resource information for a resource group."""

    resource_group: str

    @override
    @classmethod
    def action_name(cls) -> str:
        return "get_resource_group_resource_info"

    @override
    @classmethod
    def operation_type(cls) -> ActionOperationType:
        return ActionOperationType.GET


@dataclass(frozen=True)
class GetResourceInfoActionResult:
    """Result of getting resource information."""

    resource_info: ResourceInfo
