from __future__ import annotations

from dataclasses import dataclass
from typing import override

from ai.backend.common.data.entity.resource_group import ResourceGroupID
from ai.backend.manager.actions.types import ActionOperationType

from .base import ResourceGroupAction


@dataclass(frozen=True)
class GetAllowedDomainsForResourceGroupAction(ResourceGroupAction):
    """Action to get allowed domains for a resource group."""

    resource_group_id: ResourceGroupID

    @override
    @classmethod
    def action_name(cls) -> str:
        return "get_allowed_domains_for_resource_group"

    @override
    @classmethod
    def operation_type(cls) -> ActionOperationType:
        return ActionOperationType.GET


@dataclass(frozen=True)
class GetAllowedDomainsForResourceGroupActionResult:
    """Result containing the allowed domains for the resource group."""

    items: list[str]
