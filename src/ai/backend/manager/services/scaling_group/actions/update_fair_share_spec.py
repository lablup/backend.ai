from __future__ import annotations

from dataclasses import dataclass
from decimal import Decimal
from typing import override

from ai.backend.common.data.permission.types import EntityType
from ai.backend.manager.actions.action import BaseActionResult
from ai.backend.manager.actions.types import ActionOperationType
from ai.backend.manager.data.scaling_group.types import ScalingGroupData

from .base import ScalingGroupAction


@dataclass(frozen=True)
class ResourceWeightInput:
    """Input for a single resource weight entry."""

    resource_type: str
    weight: Decimal | None  # None means delete


@dataclass
class UpdateFairShareSpecAction(ScalingGroupAction):
    """Action to update fair share spec for a scaling group.

    Supports partial updates - only provided fields are modified.
    Validates resource_weights against capacity and filters out
    resource types no longer available.
    """

    @override
    @classmethod
    def entity_type(cls) -> EntityType:
        return EntityType.RESOURCE_GROUP_FAIR_SHARE

    resource_group: str
    half_life_days: int | None = None
    lookback_days: int | None = None
    decay_unit_days: int | None = None
    default_weight: Decimal | None = None
    resource_weights: list[ResourceWeightInput] | None = None

    @override
    @classmethod
    def operation_type(cls) -> ActionOperationType:
        return ActionOperationType.UPDATE

    @override
    def entity_id(self) -> str:
        return self.resource_group


@dataclass
class UpdateFairShareSpecActionResult(BaseActionResult):
    """Result of updating fair share spec."""

    scaling_group: ScalingGroupData

    @override
    def entity_id(self) -> str | None:
        return self.scaling_group.name
