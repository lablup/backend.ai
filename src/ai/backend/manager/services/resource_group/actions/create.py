from __future__ import annotations

from dataclasses import dataclass
from typing import override

from ai.backend.manager.actions.types import ActionOperationType
from ai.backend.manager.data.resource_group.types import ResourceGroupData
from ai.backend.manager.models.resource_group.creators import ResourceGroupCreator

from .base import ResourceGroupGlobalAction


@dataclass(frozen=True)
class CreateResourceGroupAction(ResourceGroupGlobalAction):
    """Action to create a resource group."""

    creator: ResourceGroupCreator

    @override
    @classmethod
    def action_name(cls) -> str:
        return "global_create_resource_group"

    @override
    @classmethod
    def operation_type(cls) -> ActionOperationType:
        return ActionOperationType.CREATE


@dataclass(frozen=True)
class CreateResourceGroupActionResult:
    """Result of creating a resource group."""

    resource_group: ResourceGroupData
