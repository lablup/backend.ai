from __future__ import annotations

from dataclasses import dataclass
from typing import override

from ai.backend.manager.actions.types import ActionOperationType

from .user_group_base import ResourceGroupUserGroupAction


@dataclass(frozen=True)
class GetAllowedResourceGroupsForProjectAction(ResourceGroupUserGroupAction):
    """Action to get the resource groups a project may schedule on."""

    @override
    @classmethod
    def action_name(cls) -> str:
        return "get_allowed_resource_groups_for_project"

    @override
    @classmethod
    def operation_type(cls) -> ActionOperationType:
        return ActionOperationType.GET


@dataclass(frozen=True)
class GetAllowedResourceGroupsForProjectActionResult:
    """Result containing the allowed resource group names for the project."""

    items: list[str]
