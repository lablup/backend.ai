from __future__ import annotations

from dataclasses import dataclass, field
from typing import override

from ai.backend.common.identifier.resource_group import ResourceGroupID, ResourceGroupName
from ai.backend.manager.actions.action import BaseActionResult
from ai.backend.manager.actions.types import ActionOperationType
from ai.backend.manager.services.scaling_group.actions.base import ScalingGroupAction


@dataclass(frozen=True)
class ResolveResourceGroupIDsByNamesAction(ScalingGroupAction):
    """Action to resolve resource group row IDs from their names in bulk."""

    names: list[ResourceGroupName] = field(default_factory=list)

    @override
    def entity_id(self) -> str | None:
        return None

    @override
    @classmethod
    def operation_type(cls) -> ActionOperationType:
        return ActionOperationType.GET


@dataclass(frozen=True)
class ResolveResourceGroupIDsByNamesActionResult(BaseActionResult):
    """Result mapping each existing resource group name to its row ID.

    Names that do not exist are absent from the mapping; the caller decides
    whether a missing name is an error.
    """

    ids_by_name: dict[ResourceGroupName, ResourceGroupID]

    @override
    def entity_id(self) -> str | None:
        return None
