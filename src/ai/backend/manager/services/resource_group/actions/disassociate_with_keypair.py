from __future__ import annotations

from dataclasses import dataclass
from typing import override

from ai.backend.manager.actions.types import ActionOperationType
from ai.backend.manager.models.resource_group import ResourceGroupForKeypairsRow
from ai.backend.manager.repositories.base.purger import BatchPurger

from .keypair_base import ResourceGroupKeypairAction


@dataclass(frozen=True)
class DisassociateResourceGroupWithKeypairsAction(ResourceGroupKeypairAction):
    """Action to disassociate a resource group from multiple keypairs."""

    purger: BatchPurger[ResourceGroupForKeypairsRow]

    @override
    @classmethod
    def action_name(cls) -> str:
        return "disassociate_resource_group_from_keypairs"

    @override
    @classmethod
    def operation_type(cls) -> ActionOperationType:
        return ActionOperationType.DELETE


@dataclass(frozen=True)
class DisassociateResourceGroupWithKeypairsActionResult:
    """Result of disassociating a resource group from keypairs."""
