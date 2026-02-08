from __future__ import annotations

from dataclasses import dataclass
from typing import override

from ai.backend.manager.actions.action import BaseActionResult
from ai.backend.manager.actions.types import ActionOperationType
from ai.backend.manager.models.scaling_group import ScalingGroupForDomainRow
from ai.backend.manager.repositories.base.creator import BulkCreator

from .domain_base import ScalingGroupDomainAction


@dataclass
class AssociateScalingGroupWithDomainsAction(ScalingGroupDomainAction):
    """Action to associate a scaling group with multiple domains."""

    bulk_creator: BulkCreator[ScalingGroupForDomainRow]

    @override
    @classmethod
    def operation_type(cls) -> ActionOperationType:
        return ActionOperationType.CREATE

    @override
    def entity_id(self) -> str | None:
        return None


@dataclass
class AssociateScalingGroupWithDomainsActionResult(BaseActionResult):
    """Result of associating a scaling group with domains."""

    @override
    def entity_id(self) -> str | None:
        return None
