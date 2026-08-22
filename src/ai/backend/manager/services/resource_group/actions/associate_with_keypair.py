from __future__ import annotations

from dataclasses import dataclass
from typing import override

from ai.backend.manager.actions.types import ActionOperationType
from ai.backend.manager.models.resource_group import ResourceGroupForKeypairsRow
from ai.backend.manager.repositories.base.creator import BulkCreator

from .keypair_base import ResourceGroupKeypairAction


@dataclass(frozen=True)
class AssociateResourceGroupWithKeypairsAction(ResourceGroupKeypairAction):
    """Action to associate a resource group with multiple keypairs."""

    bulk_creator: BulkCreator[ResourceGroupForKeypairsRow]

    @override
    @classmethod
    def action_name(cls) -> str:
        return "associate_resource_group_with_keypairs"

    @override
    @classmethod
    def operation_type(cls) -> ActionOperationType:
        return ActionOperationType.CREATE


@dataclass(frozen=True)
class AssociateResourceGroupWithKeypairsActionResult:
    """Result of associating a resource group with keypairs."""
