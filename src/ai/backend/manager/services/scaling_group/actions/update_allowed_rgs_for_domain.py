from __future__ import annotations

from dataclasses import dataclass, field
from typing import override

from ai.backend.manager.actions.action import BaseActionResult
from ai.backend.manager.actions.types import ActionOperationType

from .domain_base import ScalingGroupDomainAction


@dataclass(frozen=True)
class UpdateAllowedResourceGroupsForDomainAction(ScalingGroupDomainAction):
    """Action to atomically add/remove allowed resource groups for a domain."""

    domain_name: str
    add: list[str] = field(default_factory=list)
    remove: list[str] = field(default_factory=list)

    @override
    @classmethod
    def operation_type(cls) -> ActionOperationType:
        return ActionOperationType.UPDATE

    @override
    def entity_id(self) -> str | None:
        return self.domain_name


@dataclass(frozen=True)
class UpdateAllowedResourceGroupsForDomainActionResult(BaseActionResult):
    """Result containing the current allowed resource groups for the domain."""

    allowed_resource_groups: list[str]

    @override
    def entity_id(self) -> str | None:
        return None
