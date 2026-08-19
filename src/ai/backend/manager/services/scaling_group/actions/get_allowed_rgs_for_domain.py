from __future__ import annotations

from dataclasses import dataclass
from typing import override

from ai.backend.manager.actions.types import ActionOperationType

from .domain_base import ScalingGroupDomainAction


@dataclass(frozen=True)
class GetAllowedResourceGroupsForDomainAction(ScalingGroupDomainAction):
    """Action to get allowed resource groups for a domain."""

    domain_name: str

    @override
    @classmethod
    def action_name(cls) -> str:
        return "get_allowed_resource_groups_for_domain"

    @override
    @classmethod
    def operation_type(cls) -> ActionOperationType:
        return ActionOperationType.GET


@dataclass(frozen=True)
class GetAllowedResourceGroupsForDomainActionResult:
    """Result containing the allowed resource groups for the domain."""

    items: list[str]
