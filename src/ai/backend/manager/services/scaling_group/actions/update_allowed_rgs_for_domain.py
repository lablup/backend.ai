from __future__ import annotations

from dataclasses import dataclass, field
from typing import override

from ai.backend.common.data.entity.resource_group import ResourceGroupID
from ai.backend.manager.actions.types import ActionOperationType

from .domain_base import ScalingGroupDomainAction


@dataclass(frozen=True)
class UpdateAllowedResourceGroupsForDomainAction(ScalingGroupDomainAction):
    """Action to atomically add/remove allowed resource groups for a domain."""

    domain_name: str
    add: list[ResourceGroupID] = field(default_factory=list)
    remove: list[ResourceGroupID] = field(default_factory=list)

    @override
    @classmethod
    def action_name(cls) -> str:
        return "update_allowed_resource_groups_for_domain"

    @override
    @classmethod
    def operation_type(cls) -> ActionOperationType:
        return ActionOperationType.UPDATE


@dataclass(frozen=True)
class UpdateAllowedResourceGroupsForDomainActionResult:
    """Result containing the current allowed resource groups for the domain."""

    allowed_resource_groups: list[str]
