from __future__ import annotations

from dataclasses import dataclass
from typing import override

from ai.backend.manager.actions.types import ActionOperationType
from ai.backend.manager.models.resource_group import ResourceGroupForProjectRow
from ai.backend.manager.repositories.base.rbac.scope_binder import RBACScopeBinder

from .user_group_base import ResourceGroupUserGroupAction


@dataclass(frozen=True)
class AssociateResourceGroupWithUserGroupsAction(ResourceGroupUserGroupAction):
    """Action to associate a resource group with multiple user groups (projects)."""

    binder: RBACScopeBinder[ResourceGroupForProjectRow]

    @override
    @classmethod
    def action_name(cls) -> str:
        return "associate_resource_group_with_projects"

    @override
    @classmethod
    def operation_type(cls) -> ActionOperationType:
        return ActionOperationType.CREATE


@dataclass(frozen=True)
class AssociateResourceGroupWithUserGroupsActionResult:
    """Result of associating a resource group with user groups."""
