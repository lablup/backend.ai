"""Type definitions for resource preset DB source."""

from __future__ import annotations

from dataclasses import dataclass
from typing import Mapping

from ai.backend.common.types import ResourceSlot, SlotName, SlotTypes
from ai.backend.manager.data.resource_preset.types import ResourcePresetData


@dataclass
class KeypairResourceData:
    """Resource data for a keypair."""

    limits: ResourceSlot
    occupied: ResourceSlot
    remaining: ResourceSlot
    group_limits: ResourceSlot
    group_occupied: ResourceSlot
    group_remaining: ResourceSlot
    scaling_group_remaining: ResourceSlot


@dataclass
class PerScalingGroupResourceData:
    """Resource data per scaling group."""

    using: ResourceSlot
    remaining: ResourceSlot


@dataclass
class PresetAllocatabilityData:
    """Preset with allocatability information."""

    preset: ResourcePresetData
    allocatable: bool


@dataclass
class CheckPresetsDBData:
    """All data fetched from DB for checking presets."""

    known_slot_types: Mapping[SlotName, SlotTypes]
    keypair_data: KeypairResourceData
    per_sgroup_data: dict[str, PerScalingGroupResourceData]
    presets: list[PresetAllocatabilityData]
