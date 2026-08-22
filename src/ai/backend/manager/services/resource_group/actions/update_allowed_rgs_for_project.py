from __future__ import annotations

from dataclasses import dataclass, field
from typing import override

from ai.backend.common.data.entity.resource_group import ResourceGroupID
from ai.backend.manager.actions.types import ActionOperationType

from .user_group_base import ResourceGroupUserGroupAction


@dataclass(frozen=True)
class UpdateAllowedResourceGroupsForProjectAction(ResourceGroupUserGroupAction):
    """Action to atomically add/remove allowed resource groups for a project."""

    add: list[ResourceGroupID] = field(default_factory=list)
    remove: list[ResourceGroupID] = field(default_factory=list)

    @override
    @classmethod
    def action_name(cls) -> str:
        return "update_allowed_resource_groups_for_project"

    @override
    @classmethod
    def operation_type(cls) -> ActionOperationType:
        return ActionOperationType.UPDATE


@dataclass(frozen=True)
class UpdateAllowedResourceGroupsForProjectActionResult:
    """Result containing the current allowed resource groups for the project."""

    allowed_resource_groups: list[str]
