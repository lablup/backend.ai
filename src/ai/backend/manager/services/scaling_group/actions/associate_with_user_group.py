from __future__ import annotations

from dataclasses import dataclass
from typing import Optional, override

from ai.backend.manager.actions.action import BaseActionResult
from ai.backend.manager.models.scaling_group import ScalingGroupForProjectRow
from ai.backend.manager.repositories.base.creator import Creator

from .base import ScalingGroupAction


@dataclass
class AssociateScalingGroupWithUserGroupAction(ScalingGroupAction):
    """Action to associate a single scaling group with a user group (project)."""

    creator: Creator[ScalingGroupForProjectRow]

    @override
    @classmethod
    def operation_type(cls) -> str:
        return "associate_with_user_group"

    @override
    def entity_id(self) -> Optional[str]:
        return None


@dataclass
class AssociateScalingGroupWithUserGroupActionResult(BaseActionResult):
    """Result of associating a scaling group with a user group."""

    @override
    def entity_id(self) -> Optional[str]:
        return None
