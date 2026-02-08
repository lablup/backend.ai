from __future__ import annotations

from dataclasses import dataclass
from typing import override

from ai.backend.manager.actions.action import BaseActionResult
from ai.backend.manager.actions.types import ActionOperationType
from ai.backend.manager.models.scaling_group import ScalingGroupForKeypairsRow
from ai.backend.manager.repositories.base.purger import BatchPurger

from .keypair_base import ScalingGroupKeypairAction


@dataclass
class DisassociateScalingGroupWithKeypairsAction(ScalingGroupKeypairAction):
    """Action to disassociate a scaling group from multiple keypairs."""

    purger: BatchPurger[ScalingGroupForKeypairsRow]

    @override
    @classmethod
    def operation_type(cls) -> ActionOperationType:
        return ActionOperationType.DELETE

    @override
    def entity_id(self) -> str | None:
        return None


@dataclass
class DisassociateScalingGroupWithKeypairsActionResult(BaseActionResult):
    """Result of disassociating a scaling group from keypairs."""

    @override
    def entity_id(self) -> str | None:
        return None
