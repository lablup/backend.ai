from __future__ import annotations

from dataclasses import dataclass
from typing import override

from ai.backend.manager.actions.action import BaseActionResult
from ai.backend.manager.actions.types import ActionOperationType
from ai.backend.manager.models.scaling_group import ScalingGroupForProjectRow
from ai.backend.manager.repositories.base.rbac.scope_unbinder import (
    RBACScopeWideEntityUnbinder,
)

from .user_group_base import ScalingGroupUserGroupAction


@dataclass
class DisassociateScalingGroupWithUserGroupsAction(ScalingGroupUserGroupAction):
    """Action to disassociate scaling groups from a project."""

    unbinder: RBACScopeWideEntityUnbinder[ScalingGroupForProjectRow]

    @override
    @classmethod
    def operation_type(cls) -> ActionOperationType:
        return ActionOperationType.DELETE

    @override
    def entity_id(self) -> str | None:
        return None


@dataclass
class DisassociateScalingGroupWithUserGroupsActionResult(BaseActionResult):
    """Result of disassociating a scaling group from a user group."""

    @override
    def entity_id(self) -> str | None:
        return None
