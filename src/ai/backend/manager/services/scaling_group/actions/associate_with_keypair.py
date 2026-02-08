from __future__ import annotations

from dataclasses import dataclass
from typing import override

from ai.backend.manager.actions.action import BaseActionResult
from ai.backend.manager.actions.types import ActionOperationType
from ai.backend.manager.models.scaling_group import ScalingGroupForKeypairsRow
from ai.backend.manager.repositories.base.creator import BulkCreator

from .keypair_base import ScalingGroupKeypairAction


@dataclass
class AssociateScalingGroupWithKeypairsAction(ScalingGroupKeypairAction):
    """Action to associate a scaling group with multiple keypairs."""

    bulk_creator: BulkCreator[ScalingGroupForKeypairsRow]

    @override
    @classmethod
    def operation_type(cls) -> ActionOperationType:
        return ActionOperationType.CREATE

    @override
    def entity_id(self) -> str | None:
        return None


@dataclass
class AssociateScalingGroupWithKeypairsActionResult(BaseActionResult):
    """Result of associating a scaling group with keypairs."""

    @override
    def entity_id(self) -> str | None:
        return None
