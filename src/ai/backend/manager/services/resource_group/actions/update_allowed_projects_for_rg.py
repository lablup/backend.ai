from __future__ import annotations

from dataclasses import dataclass, field
from typing import override
from uuid import UUID

from ai.backend.common.data.entity.resource_group import ResourceGroupID
from ai.backend.manager.actions.types import ActionOperationType

from .base import ResourceGroupAction


@dataclass(frozen=True)
class UpdateAllowedProjectsForResourceGroupAction(ResourceGroupAction):
    """Action to atomically add/remove allowed projects for a resource group."""

    resource_group_id: ResourceGroupID
    add: list[UUID] = field(default_factory=list)
    remove: list[UUID] = field(default_factory=list)

    @override
    @classmethod
    def action_name(cls) -> str:
        return "update_allowed_projects_for_resource_group"

    @override
    @classmethod
    def operation_type(cls) -> ActionOperationType:
        return ActionOperationType.UPDATE


@dataclass(frozen=True)
class UpdateAllowedProjectsForResourceGroupActionResult:
    """Result containing the current allowed projects for the resource group."""

    allowed_projects: list[UUID]
