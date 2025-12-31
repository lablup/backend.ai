from __future__ import annotations

from dataclasses import dataclass
from typing import Optional, override

from ai.backend.manager.actions.action import BaseActionResult
from ai.backend.manager.models.scaling_group import ScalingGroupForDomainRow
from ai.backend.manager.repositories.base.creator import Creator

from .base import ScalingGroupAction


@dataclass
class AssociateScalingGroupWithDomainAction(ScalingGroupAction):
    """Action to associate a single scaling group with a domain."""

    creator: Creator[ScalingGroupForDomainRow]

    @override
    @classmethod
    def operation_type(cls) -> str:
        return "associate_with_domain"

    @override
    def entity_id(self) -> Optional[str]:
        return None


@dataclass
class AssociateScalingGroupWithDomainActionResult(BaseActionResult):
    """Result of associating a scaling group with a domain."""

    @override
    def entity_id(self) -> Optional[str]:
        return None
