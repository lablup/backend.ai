"""Type definitions for resource preset repository."""

from __future__ import annotations

from dataclasses import dataclass

from ai.backend.common.types import ResourceSlot

from .db_source.types import PerScalingGroupResourceData, PresetAllocatabilityData


@dataclass
class CheckPresetsResult:
    """Result of checking resource presets from repository."""

    presets: list[PresetAllocatabilityData]
    keypair_limits: ResourceSlot
    keypair_using: ResourceSlot
    keypair_remaining: ResourceSlot
    group_limits: ResourceSlot
    group_using: ResourceSlot
    group_remaining: ResourceSlot
    scaling_group_remaining: ResourceSlot
    scaling_groups: dict[str, PerScalingGroupResourceData]
