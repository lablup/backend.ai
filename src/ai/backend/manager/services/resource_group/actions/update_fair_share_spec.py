from __future__ import annotations

from dataclasses import dataclass
from decimal import Decimal
from typing import override

from ai.backend.manager.actions.types import ActionOperationType
from ai.backend.manager.data.resource_group.types import ResourceGroupData

from .base import ResourceGroupAction


@dataclass(frozen=True)
class ResourceWeightInput:
    """Input for a single resource weight entry."""

    resource_type: str
    weight: Decimal | None  # None means delete


@dataclass(frozen=True)
class UpdateFairShareSpecAction(ResourceGroupAction):
    """Action to update fair share spec for a resource group.

    Supports partial updates - only provided fields are modified.
    Validates resource_weights against capacity and filters out
    resource types no longer available.
    """

    resource_group: str
    half_life_days: int | None = None
    lookback_days: int | None = None
    decay_unit_days: int | None = None
    default_weight: Decimal | None = None
    resource_weights: list[ResourceWeightInput] | None = None

    @override
    @classmethod
    def action_name(cls) -> str:
        return "update_resource_group_fair_share_spec"

    @override
    @classmethod
    def operation_type(cls) -> ActionOperationType:
        return ActionOperationType.UPDATE


@dataclass(frozen=True)
class UpdateFairShareSpecActionResult:
    """Result of updating fair share spec."""

    resource_group: ResourceGroupData
