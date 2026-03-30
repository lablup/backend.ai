from __future__ import annotations

from dataclasses import dataclass, field
from typing import override
from uuid import UUID

from ai.backend.manager.actions.action import BaseActionResult
from ai.backend.manager.actions.types import ActionOperationType

from .user_group_base import ScalingGroupUserGroupAction


@dataclass(frozen=True)
class UpdateAllowedResourceGroupsForProjectAction(ScalingGroupUserGroupAction):
    """Action to atomically add/remove allowed resource groups for a project."""

    project_id: UUID
    add: list[str] = field(default_factory=list)
    remove: list[str] = field(default_factory=list)

    @override
    @classmethod
    def operation_type(cls) -> ActionOperationType:
        return ActionOperationType.UPDATE

    @override
    def entity_id(self) -> str | None:
        return str(self.project_id)


@dataclass(frozen=True)
class UpdateAllowedResourceGroupsForProjectActionResult(BaseActionResult):
    """Result containing the current allowed resource groups for the project."""

    allowed_resource_groups: list[str]

    @override
    def entity_id(self) -> str | None:
        return None
