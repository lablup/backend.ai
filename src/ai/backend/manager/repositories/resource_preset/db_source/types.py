"""Type definitions for resource preset DB source."""

from __future__ import annotations

from abc import ABC, abstractmethod
from collections.abc import Mapping
from dataclasses import dataclass
from typing import Any, override
from uuid import UUID

from ai.backend.common.types import (
    AccessKey,
    SessionTypes,
    SlotName,
    SlotQuantity,
    SlotTypes,
)
from ai.backend.manager.data.resource_preset.types import ResourcePresetData
from ai.backend.manager.models.kernel.row import KernelRow


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
    resource_group_remaining: list[SlotQuantity]


@dataclass
class PerResourceGroupResourceData:
    """Resource data per scaling group."""

    using: list[SlotQuantity]
    remaining: list[SlotQuantity]


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
    per_sgroup_data: dict[str, PerResourceGroupResourceData]
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

    @override
    def get_condition(self) -> Any:
        return KernelRow.access_key == self.access_key


class UserIdFilter(ResourceOccupancyFilter):
    """Filter for the kernel owner."""

    user_id: UUID

    def __init__(self, user_id: UUID) -> None:
        self.user_id = user_id

    @override
    def get_condition(self) -> Any:
        return KernelRow.user_uuid == self.user_id


class NonPrivateSessionFilter(ResourceOccupancyFilter):
    """Exclude private (SFTP) sessions, as the scheduler does."""

    @override
    def get_condition(self) -> Any:
        return KernelRow.session_type.not_in(SessionTypes.private_types())


class GroupIdFilter(ResourceOccupancyFilter):
    """Filter for group ID."""

    def __init__(self, group_id: UUID) -> None:
        self.group_id = group_id

    @override
    def get_condition(self) -> Any:
        return KernelRow.group_id == self.group_id


class DomainNameFilter(ResourceOccupancyFilter):
    """Filter for domain name."""

    def __init__(self, domain_name: str) -> None:
        self.domain_name = domain_name

    @override
    def get_condition(self) -> Any:
        return KernelRow.domain_name == self.domain_name
