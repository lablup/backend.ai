from __future__ import annotations

from dataclasses import dataclass
from typing import override

from ai.backend.manager.actions.types import ActionOperationType
from ai.backend.manager.models.scaling_group import ScalingGroupForProjectRow
from ai.backend.manager.repositories.base.rbac.scope_unbinder import (
    RBACScopeEntityUnbinder,
)

from .user_group_base import ScalingGroupUserGroupAction


@dataclass(frozen=True)
class DisassociateScalingGroupWithUserGroupsAction(ScalingGroupUserGroupAction):
    """Action to disassociate scaling groups from a project."""

    unbinder: RBACScopeEntityUnbinder[ScalingGroupForProjectRow]

    @override
    @classmethod
    def action_name(cls) -> str:
        return "disassociate_resource_group_from_projects"

    @override
    @classmethod
    def operation_type(cls) -> ActionOperationType:
        return ActionOperationType.DELETE


@dataclass(frozen=True)
class DisassociateScalingGroupWithUserGroupsActionResult:
    """Result of disassociating a scaling group from a user group."""
