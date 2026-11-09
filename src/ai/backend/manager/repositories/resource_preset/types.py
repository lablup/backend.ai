"""Type definitions for resource preset repository."""

from __future__ import annotations

from dataclasses import dataclass

from ai.backend.common.types import SlotQuantity

from .db_source.types import PerResourceGroupResourceData, PresetAllocatabilityData


@dataclass
class CheckPresetsResult:
    """Result of checking resource presets from repository."""

    presets: list[PresetAllocatabilityData]
    keypair_limits: list[SlotQuantity]
    keypair_using: list[SlotQuantity]
    keypair_remaining: list[SlotQuantity]
    group_limits: list[SlotQuantity]
    group_using: list[SlotQuantity]
    group_remaining: list[SlotQuantity]
    resource_group_remaining: list[SlotQuantity]
    resource_groups: dict[str, PerResourceGroupResourceData]
