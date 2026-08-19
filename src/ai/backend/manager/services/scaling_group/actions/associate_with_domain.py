from __future__ import annotations

from dataclasses import dataclass
from typing import override

from ai.backend.manager.actions.types import ActionOperationType
from ai.backend.manager.models.scaling_group import ScalingGroupForDomainRow
from ai.backend.manager.repositories.base.rbac.scope_binder import RBACScopeBinder

from .domain_base import ScalingGroupDomainAction


@dataclass(frozen=True)
class AssociateScalingGroupWithDomainsAction(ScalingGroupDomainAction):
    """Action to associate a scaling group with multiple domains."""

    binder: RBACScopeBinder[ScalingGroupForDomainRow]

    @override
    @classmethod
    def action_name(cls) -> str:
        return "associate_resource_group_with_domains"

    @override
    @classmethod
    def operation_type(cls) -> ActionOperationType:
        return ActionOperationType.CREATE


@dataclass(frozen=True)
class AssociateScalingGroupWithDomainsActionResult:
    """Result of associating a scaling group with domains."""
