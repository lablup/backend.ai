"""Type definitions for resource preset DB source."""

from __future__ import annotations

from abc import ABC, abstractmethod
from collections.abc import Mapping
from dataclasses import dataclass
from typing import Any
from uuid import UUID

from ai.backend.common.types import (
    AccessKey,
    BinarySize,
    ResourceSlot,
    SlotName,
    SlotQuantity,
    SlotTypes,
)
from ai.backend.common.types import (
    LegacyResourceSlotState as ResourceSlotState,
)
from ai.backend.manager.data.resource_preset.types import ResourcePresetData
from ai.backend.manager.models.kernel import KernelRow
from ai.backend.manager.repositories.resource_slot.types import (
    quantities_from_json,
    quantities_to_json,
)


@dataclass
class ResourceUsageData:
    """Resource usage data with limits, occupied, and remaining."""

    limits: list[SlotQuantity]
    occupied: list[SlotQuantity]
    remaining: list[SlotQuantity]


@dataclass
class KeypairResourceData:
    """Resource data for a keypair."""

    limits: list[SlotQuantity]
    occupied: list[SlotQuantity]
    remaining: list[SlotQuantity]
    group_limits: list[SlotQuantity]
    group_occupied: list[SlotQuantity]
    group_remaining: list[SlotQuantity]
    scaling_group_remaining: list[SlotQuantity]


@dataclass
class PerScalingGroupResourceData:
    """Resource data per scaling group."""

    using: list[SlotQuantity]
    remaining: list[SlotQuantity]

    def to_cache(self) -> dict[str, Any]:
        """Serialize to cache-friendly format."""
        return {
            str(ResourceSlotState.OCCUPIED): quantities_to_json(self.using),
            str(ResourceSlotState.AVAILABLE): quantities_to_json(self.remaining),
        }

    @classmethod
    def from_cache(cls, data: dict[str, Any]) -> PerScalingGroupResourceData:
        """Deserialize from cache format."""
        return cls(
            using=quantities_from_json(data[ResourceSlotState.OCCUPIED]),
            remaining=quantities_from_json(data[ResourceSlotState.AVAILABLE]),
        )


@dataclass
class PresetAllocatabilityData:
    """Preset with allocatability information."""

    preset: ResourcePresetData
    allocatable: bool

    def to_cache(self) -> dict[str, Any]:
        """Serialize to cache-friendly format."""
        return {
            "preset": {
                "id": str(self.preset.id),
                "name": self.preset.name,
                "resource_slots": self.preset.resource_slots.to_json(),
                "shared_memory": str(self.preset.shared_memory)
                if self.preset.shared_memory is not None
                else None,
                "scaling_group_name": self.preset.scaling_group_name,
            },
            "allocatable": self.allocatable,
        }

    @classmethod
    def from_cache(cls, data: dict[str, Any]) -> PresetAllocatabilityData:
        """Deserialize from cache format."""
        return cls(
            preset=ResourcePresetData(
                id=UUID(data["preset"]["id"]),
                name=data["preset"]["name"],
                resource_slots=ResourceSlot.from_json(data["preset"]["resource_slots"]),
                shared_memory=int(BinarySize.from_str(data["preset"]["shared_memory"]))
                if data["preset"]["shared_memory"] is not None
                else None,
                scaling_group_name=data["preset"]["scaling_group_name"],
            ),
            allocatable=data["allocatable"],
        )


@dataclass
class CheckPresetsDBData:
    """All data fetched from DB for checking presets."""

    known_slot_types: Mapping[SlotName, SlotTypes]
    keypair_data: KeypairResourceData
    per_sgroup_data: dict[str, PerScalingGroupResourceData]
    presets: list[PresetAllocatabilityData]


class ResourceOccupancyFilter(ABC):
    """Abstract base class for resource occupancy filters."""

    @abstractmethod
    def get_condition(self) -> Any:
        """Return SQLAlchemy condition for this filter."""
        pass


class AccessKeyFilter(ResourceOccupancyFilter):
    """Filter for access key."""

    def __init__(self, access_key: AccessKey) -> None:
        self.access_key = access_key

    def get_condition(self) -> Any:
        return KernelRow.access_key == self.access_key


class GroupIdFilter(ResourceOccupancyFilter):
    """Filter for group ID."""

    def __init__(self, group_id: UUID) -> None:
        self.group_id = group_id

    def get_condition(self) -> Any:
        return KernelRow.group_id == self.group_id


class DomainNameFilter(ResourceOccupancyFilter):
    """Filter for domain name."""

    def __init__(self, domain_name: str) -> None:
        self.domain_name = domain_name

    def get_condition(self) -> Any:
        return KernelRow.domain_name == self.domain_name
