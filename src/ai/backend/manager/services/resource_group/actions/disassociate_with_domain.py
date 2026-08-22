from __future__ import annotations

from dataclasses import dataclass
from typing import override

from ai.backend.manager.actions.types import ActionOperationType
from ai.backend.manager.models.resource_group import ResourceGroupForDomainRow
from ai.backend.manager.repositories.base.rbac.scope_unbinder import (
    RBACScopeEntityUnbinder,
)

from .domain_base import ResourceGroupDomainAction


@dataclass(frozen=True)
class DisassociateResourceGroupWithDomainsAction(ResourceGroupDomainAction):
    """Action to disassociate resource groups from a domain."""

    unbinder: RBACScopeEntityUnbinder[ResourceGroupForDomainRow]

    @override
    @classmethod
    def action_name(cls) -> str:
        return "disassociate_resource_group_from_domains"

    @override
    @classmethod
    def operation_type(cls) -> ActionOperationType:
        return ActionOperationType.DELETE


@dataclass(frozen=True)
class DisassociateResourceGroupWithDomainsActionResult:
    """Result of disassociating a resource group from domains."""
