from __future__ import annotations

from dataclasses import dataclass
from typing import override

from ai.backend.manager.actions.types import ActionOperationType
from ai.backend.manager.data.resource_group.types import ResourceGroupData
from ai.backend.manager.services.resource_group.actions.base import ResourceGroupAction


@dataclass(frozen=True)
class PurgeResourceGroupAction(ResourceGroupAction):
    """Action to purge a resource group, including all related sessions and routes."""

    @override
    @classmethod
    def action_name(cls) -> str:
        return "purge_resource_group"

    @override
    @classmethod
    def operation_type(cls) -> ActionOperationType:
        return ActionOperationType.PURGE


@dataclass(frozen=True)
class PurgeResourceGroupActionResult:
    """Result of purging a resource group."""

    data: ResourceGroupData
