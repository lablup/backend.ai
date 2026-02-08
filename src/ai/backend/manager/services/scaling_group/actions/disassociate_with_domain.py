from __future__ import annotations

from dataclasses import dataclass
from typing import override

from ai.backend.manager.actions.action import BaseActionResult
from ai.backend.manager.actions.types import ActionOperationType
from ai.backend.manager.models.scaling_group import ScalingGroupForDomainRow
from ai.backend.manager.repositories.base.purger import BatchPurger

from .domain_base import ScalingGroupDomainAction


@dataclass
class DisassociateScalingGroupWithDomainsAction(ScalingGroupDomainAction):
    """Action to disassociate a scaling group from multiple domains."""

    purger: BatchPurger[ScalingGroupForDomainRow]

    @override
    @classmethod
    def operation_type(cls) -> ActionOperationType:
        return ActionOperationType.DELETE

    @override
    def entity_id(self) -> str | None:
        return None


@dataclass
class DisassociateScalingGroupWithDomainsActionResult(BaseActionResult):
    """Result of disassociating a scaling group from domains."""

    @override
    def entity_id(self) -> str | None:
        return None
