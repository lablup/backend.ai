from __future__ import annotations

from dataclasses import dataclass
from typing import override

from ai.backend.manager.actions.types import ActionOperationType
from ai.backend.manager.models.scaling_group import ScalingGroupForDomainRow
from ai.backend.manager.repositories.base.rbac.scope_unbinder import (
    RBACScopeEntityUnbinder,
)

from .domain_base import ScalingGroupDomainAction


@dataclass(frozen=True)
class DisassociateScalingGroupWithDomainsAction(ScalingGroupDomainAction):
    """Action to disassociate scaling groups from a domain."""

    unbinder: RBACScopeEntityUnbinder[ScalingGroupForDomainRow]

    @override
    @classmethod
    def action_name(cls) -> str:
        return "disassociate_resource_group_from_domains"

    @override
    @classmethod
    def operation_type(cls) -> ActionOperationType:
        return ActionOperationType.DELETE


@dataclass(frozen=True)
class DisassociateScalingGroupWithDomainsActionResult:
    """Result of disassociating a scaling group from domains."""
