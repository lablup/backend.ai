from __future__ import annotations

from dataclasses import dataclass
from typing import override

from ai.backend.manager.actions.types import ActionOperationType
from ai.backend.manager.models.scaling_group import ScalingGroupForProjectRow
from ai.backend.manager.repositories.base.rbac.scope_binder import RBACScopeBinder

from .user_group_base import ScalingGroupUserGroupAction


@dataclass(frozen=True)
class AssociateScalingGroupWithUserGroupsAction(ScalingGroupUserGroupAction):
    """Action to associate a scaling group with multiple user groups (projects)."""

    binder: RBACScopeBinder[ScalingGroupForProjectRow]

    @override
    @classmethod
    def action_name(cls) -> str:
        return "associate_resource_group_with_projects"

    @override
    @classmethod
    def operation_type(cls) -> ActionOperationType:
        return ActionOperationType.CREATE


@dataclass(frozen=True)
class AssociateScalingGroupWithUserGroupsActionResult:
    """Result of associating a scaling group with user groups."""
