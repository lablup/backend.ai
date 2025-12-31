from __future__ import annotations

from dataclasses import dataclass
from typing import Optional, override

from ai.backend.manager.actions.action import BaseActionResult
from ai.backend.manager.models.scaling_group import ScalingGroupForDomainRow
from ai.backend.manager.repositories.base.purger import BatchPurger

from .base import ScalingGroupAction


@dataclass
class DisassociateScalingGroupWithDomainAction(ScalingGroupAction):
    """Action to disassociate a single scaling group from a domain."""

    purger: BatchPurger[ScalingGroupForDomainRow]

    @override
    @classmethod
    def operation_type(cls) -> str:
        return "disassociate_with_domain"

    @override
    def entity_id(self) -> Optional[str]:
        return None


@dataclass
class DisassociateScalingGroupWithDomainActionResult(BaseActionResult):
    """Result of disassociating a scaling group from a domain."""

    @override
    def entity_id(self) -> Optional[str]:
        return None
