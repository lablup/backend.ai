from __future__ import annotations

from dataclasses import dataclass
from typing import override

from ai.backend.manager.actions.action import BaseActionResult
from ai.backend.manager.models.scaling_group import ScalingGroupForProjectRow
from ai.backend.manager.repositories.base.purger import BatchPurger

from .base import ScalingGroupAction


@dataclass
class DisassociateScalingGroupWithUserGroupsAction(ScalingGroupAction):
    """Action to disassociate a single scaling group from a user group (project)."""

    purger: BatchPurger[ScalingGroupForProjectRow]

    @override
    @classmethod
    def operation_type(cls) -> str:
        return "disassociate_with_user_groups"

    @override
    def entity_id(self) -> str | None:
        return None


@dataclass
class DisassociateScalingGroupWithUserGroupsActionResult(BaseActionResult):
    """Result of disassociating a scaling group from a user group."""

    @override
    def entity_id(self) -> str | None:
        return None
