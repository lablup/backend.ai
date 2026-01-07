from __future__ import annotations

from dataclasses import dataclass
from typing import Optional, override

from ai.backend.manager.actions.action import BaseActionResult
from ai.backend.manager.models.scaling_group import ScalingGroupForDomainRow
from ai.backend.manager.repositories.base.creator import BulkCreator

from .base import ScalingGroupAction


@dataclass
class AssociateScalingGroupWithDomainsAction(ScalingGroupAction):
    """Action to associate a scaling group with multiple domains."""

    bulk_creator: BulkCreator[ScalingGroupForDomainRow]

    @override
    @classmethod
    def operation_type(cls) -> str:
        return "associate_with_domains"

    @override
    def entity_id(self) -> Optional[str]:
        return None


@dataclass
class AssociateScalingGroupWithDomainsActionResult(BaseActionResult):
    """Result of associating a scaling group with domains."""

    @override
    def entity_id(self) -> Optional[str]:
        return None
