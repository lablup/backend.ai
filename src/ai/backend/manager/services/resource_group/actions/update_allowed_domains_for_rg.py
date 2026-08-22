from __future__ import annotations

from dataclasses import dataclass, field
from typing import override

from ai.backend.common.data.entity.resource_group import ResourceGroupID
from ai.backend.manager.actions.types import ActionOperationType

from .base import ResourceGroupAction


@dataclass(frozen=True)
class UpdateAllowedDomainsForResourceGroupAction(ResourceGroupAction):
    """Action to atomically add/remove allowed domains for a resource group."""

    resource_group_id: ResourceGroupID
    add: list[str] = field(default_factory=list)
    remove: list[str] = field(default_factory=list)

    @override
    @classmethod
    def action_name(cls) -> str:
        return "update_allowed_domains_for_resource_group"

    @override
    @classmethod
    def operation_type(cls) -> ActionOperationType:
        return ActionOperationType.UPDATE


@dataclass(frozen=True)
class UpdateAllowedDomainsForResourceGroupActionResult:
    """Result containing the current allowed domains for the resource group."""

    allowed_domains: list[str]
