from __future__ import annotations

from dataclasses import dataclass
from typing import override

from ai.backend.manager.actions.types import ActionOperationType

from .user_group_base import ScalingGroupUserGroupAction


@dataclass(frozen=True)
class GetAllowedResourceGroupsForProjectAction(ScalingGroupUserGroupAction):
    """Action to get allowed resource groups for a project."""

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
    """Result containing the allowed resource groups for the project."""

    items: list[str]
