from __future__ import annotations

from dataclasses import dataclass
from typing import override

from ai.backend.manager.actions.types import ActionOperationType

from .base import ResourceGroupGlobalAction


@dataclass(frozen=True)
class ListAllowedResourceGroupsAction(ResourceGroupGlobalAction):
    """Action to list resource groups allowed for a user."""

    domain_name: str
    group: str
    access_key: str
    is_admin: bool

    @override
    @classmethod
    def action_name(cls) -> str:
        return "global_list_allowed_resource_groups"

    @override
    @classmethod
    def operation_type(cls) -> ActionOperationType:
        return ActionOperationType.SEARCH


@dataclass(frozen=True)
class ListAllowedResourceGroupsActionResult:
    """Result of listing allowed resource groups."""

    resource_group_names: list[str]
