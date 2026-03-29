from __future__ import annotations

from dataclasses import dataclass
from typing import override

from ai.backend.manager.actions.action import BaseActionResult
from ai.backend.manager.actions.types import ActionOperationType

from .domain_base import ScalingGroupDomainAction


@dataclass(frozen=True)
class GetAllowedResourceGroupsForDomainAction(ScalingGroupDomainAction):
    """Action to get allowed resource groups for a domain."""

    domain_name: str

    @override
    @classmethod
    def operation_type(cls) -> ActionOperationType:
        return ActionOperationType.GET

    @override
    def entity_id(self) -> str | None:
        return self.domain_name


@dataclass(frozen=True)
class GetAllowedResourceGroupsForDomainActionResult(BaseActionResult):
    """Result containing the allowed resource groups for the domain."""

    items: list[str]

    @override
    def entity_id(self) -> str | None:
        return None
