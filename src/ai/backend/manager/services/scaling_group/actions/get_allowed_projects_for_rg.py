from __future__ import annotations

from dataclasses import dataclass
from typing import override
from uuid import UUID

from ai.backend.manager.actions.action import BaseActionResult
from ai.backend.manager.actions.types import ActionOperationType

from .base import ScalingGroupAction


@dataclass(frozen=True)
class GetAllowedProjectsForResourceGroupAction(ScalingGroupAction):
    """Action to get allowed projects for a resource group."""

    resource_group_name: str

    @override
    @classmethod
    def operation_type(cls) -> ActionOperationType:
        return ActionOperationType.GET

    @override
    def entity_id(self) -> str | None:
        return self.resource_group_name


@dataclass(frozen=True)
class GetAllowedProjectsForResourceGroupActionResult(BaseActionResult):
    """Result containing the allowed projects for the resource group."""

    items: list[UUID]

    @override
    def entity_id(self) -> str | None:
        return None
