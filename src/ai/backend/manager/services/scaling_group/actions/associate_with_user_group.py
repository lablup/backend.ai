from __future__ import annotations

from dataclasses import dataclass
from typing import override

from ai.backend.manager.actions.action import BaseActionResult
from ai.backend.manager.actions.types import ActionOperationType
from ai.backend.manager.models.scaling_group import ScalingGroupForProjectRow
from ai.backend.manager.repositories.base.creator import BulkCreator

from .user_group_base import ScalingGroupUserGroupAction


@dataclass
class AssociateScalingGroupWithUserGroupsAction(ScalingGroupUserGroupAction):
    """Action to associate a scaling group with multiple user groups (projects)."""

    bulk_creator: BulkCreator[ScalingGroupForProjectRow]

    @override
    @classmethod
    def operation_type(cls) -> ActionOperationType:
        return ActionOperationType.CREATE

    @override
    def entity_id(self) -> str | None:
        return None


@dataclass
class AssociateScalingGroupWithUserGroupsActionResult(BaseActionResult):
    """Result of associating a scaling group with user groups."""

    @override
    def entity_id(self) -> str | None:
        return None
