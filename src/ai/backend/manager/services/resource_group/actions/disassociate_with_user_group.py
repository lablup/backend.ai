from __future__ import annotations

from dataclasses import dataclass
from typing import override

from ai.backend.manager.actions.types import ActionOperationType
from ai.backend.manager.models.resource_group import ResourceGroupForProjectRow
from ai.backend.manager.repositories.base.rbac.scope_unbinder import (
    RBACScopeEntityUnbinder,
)

from .user_group_base import ResourceGroupUserGroupAction


@dataclass(frozen=True)
class DisassociateResourceGroupWithUserGroupsAction(ResourceGroupUserGroupAction):
    """Action to disassociate resource groups from a project."""

    unbinder: RBACScopeEntityUnbinder[ResourceGroupForProjectRow]

    @override
    @classmethod
    def action_name(cls) -> str:
        return "disassociate_resource_group_from_projects"

    @override
    @classmethod
    def operation_type(cls) -> ActionOperationType:
        return ActionOperationType.DELETE


@dataclass(frozen=True)
class DisassociateResourceGroupWithUserGroupsActionResult:
    """Result of disassociating a resource group from a user group."""
