from __future__ import annotations

from dataclasses import dataclass
from typing import override

from ai.backend.manager.actions.types import ActionOperationType
from ai.backend.manager.data.resource_group.types import ResourceGroupData
from ai.backend.manager.models.resource_group import ResourceGroupRow
from ai.backend.manager.repositories.base.updater import Updater

from .base import ResourceGroupAction


@dataclass(frozen=True)
class UpdateResourceGroupAction(ResourceGroupAction):
    """Action to modify a resource group."""

    updater: Updater[ResourceGroupRow]

    @override
    @classmethod
    def action_name(cls) -> str:
        return "update_resource_group"

    @override
    @classmethod
    def operation_type(cls) -> ActionOperationType:
        return ActionOperationType.UPDATE


@dataclass(frozen=True)
class UpdateResourceGroupActionResult:
    """Result of modifying a resource group."""

    resource_group: ResourceGroupData
