from __future__ import annotations

from dataclasses import dataclass
from typing import Optional, override

from ai.backend.manager.actions.action import BaseActionResult
from ai.backend.manager.models.scaling_group import ScalingGroupForKeypairsRow
from ai.backend.manager.repositories.base.creator import BulkCreator

from .base import ScalingGroupAction


@dataclass
class AssociateScalingGroupWithKeypairsAction(ScalingGroupAction):
    """Action to associate a scaling group with multiple keypairs."""

    bulk_creator: BulkCreator[ScalingGroupForKeypairsRow]

    @override
    @classmethod
    def operation_type(cls) -> str:
        return "associate_with_keypairs"

    @override
    def entity_id(self) -> Optional[str]:
        return None


@dataclass
class AssociateScalingGroupWithKeypairsActionResult(BaseActionResult):
    """Result of associating a scaling group with keypairs."""

    @override
    def entity_id(self) -> Optional[str]:
        return None
