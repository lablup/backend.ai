from __future__ import annotations

from dataclasses import dataclass
from typing import override
from uuid import UUID

from ai.backend.manager.actions.action import BaseActionResult
from ai.backend.manager.actions.types import ActionOperationType

from .user_group_base import ScalingGroupUserGroupAction


@dataclass(frozen=True)
class GetAllowedResourceGroupsForProjectAction(ScalingGroupUserGroupAction):
    """Action to get allowed resource groups for a project."""

    project_id: UUID

    @override
    @classmethod
    def operation_type(cls) -> ActionOperationType:
        return ActionOperationType.GET

    @override
    def entity_id(self) -> str | None:
        return str(self.project_id)


@dataclass(frozen=True)
class GetAllowedResourceGroupsForProjectActionResult(BaseActionResult):
    """Result containing the allowed resource groups for the project."""

    items: list[str]

    @override
    def entity_id(self) -> str | None:
        return None
