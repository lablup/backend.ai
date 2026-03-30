from __future__ import annotations

from dataclasses import dataclass, field
from typing import override

from ai.backend.manager.actions.action import BaseActionResult
from ai.backend.manager.actions.types import ActionOperationType

from .base import ScalingGroupAction


@dataclass(frozen=True)
class UpdateAllowedDomainsForResourceGroupAction(ScalingGroupAction):
    """Action to atomically add/remove allowed domains for a resource group."""

    resource_group_name: str
    add: list[str] = field(default_factory=list)
    remove: list[str] = field(default_factory=list)

    @override
    @classmethod
    def operation_type(cls) -> ActionOperationType:
        return ActionOperationType.UPDATE

    @override
    def entity_id(self) -> str | None:
        return self.resource_group_name


@dataclass(frozen=True)
class UpdateAllowedDomainsForResourceGroupActionResult(BaseActionResult):
    """Result containing the current allowed domains for the resource group."""

    allowed_domains: list[str]

    @override
    def entity_id(self) -> str | None:
        return None
