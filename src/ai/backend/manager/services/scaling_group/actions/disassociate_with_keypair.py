from __future__ import annotations

from dataclasses import dataclass
from typing import override

from ai.backend.manager.actions.types import ActionOperationType
from ai.backend.manager.models.scaling_group import ScalingGroupForKeypairsRow
from ai.backend.manager.repositories.base.purger import BatchPurger

from .keypair_base import ScalingGroupKeypairAction


@dataclass(frozen=True)
class DisassociateScalingGroupWithKeypairsAction(ScalingGroupKeypairAction):
    """Action to disassociate a scaling group from multiple keypairs."""

    purger: BatchPurger[ScalingGroupForKeypairsRow]

    @override
    @classmethod
    def action_name(cls) -> str:
        return "disassociate_resource_group_from_keypairs"

    @override
    @classmethod
    def operation_type(cls) -> ActionOperationType:
        return ActionOperationType.DELETE


@dataclass(frozen=True)
class DisassociateScalingGroupWithKeypairsActionResult:
    """Result of disassociating a scaling group from keypairs."""
