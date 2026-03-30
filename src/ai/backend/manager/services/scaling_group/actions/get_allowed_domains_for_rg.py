from __future__ import annotations

from dataclasses import dataclass
from typing import override

from ai.backend.manager.actions.action import BaseActionResult
from ai.backend.manager.actions.types import ActionOperationType

from .base import ScalingGroupAction


@dataclass(frozen=True)
class GetAllowedDomainsForResourceGroupAction(ScalingGroupAction):
    """Action to get allowed domains for a resource group."""

    resource_group_name: str

    @override
    @classmethod
    def operation_type(cls) -> ActionOperationType:
        return ActionOperationType.GET

    @override
    def entity_id(self) -> str | None:
        return self.resource_group_name


@dataclass(frozen=True)
class GetAllowedDomainsForResourceGroupActionResult(BaseActionResult):
    """Result containing the allowed domains for the resource group."""

    items: list[str]

    @override
    def entity_id(self) -> str | None:
        return None
