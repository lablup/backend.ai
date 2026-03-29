"""Domain types for resource allocation operations."""

from __future__ import annotations

from collections.abc import Mapping
from dataclasses import dataclass
from typing import Any

from ai.backend.common.types import AccessKey, SlotQuantity
from ai.backend.manager.data.resource_preset.types import ResourcePresetData


@dataclass(frozen=True)
class ScopeUsageData:
    """Resource usage within a single scope (keypair, project, or domain)."""

    limits: list[SlotQuantity]
    used: list[SlotQuantity]
    assignable: list[SlotQuantity]  # limits - used


@dataclass(frozen=True)
class ResourceGroupUsageData:
    """Resource usage within a resource group (scaling group)."""

    capacity: list[SlotQuantity]
    used: list[SlotQuantity]
    free: list[SlotQuantity]
    max_per_node: list[SlotQuantity]  # largest single agent free


@dataclass(frozen=True)
class EffectiveAllocationData:
    """Effective resource allocation across all scopes."""

    assignable: list[SlotQuantity]  # min(all scopes)
    keypair: ScopeUsageData
    project: ScopeUsageData | None  # None when group_resource_visibility=false
    domain: ScopeUsageData
    resource_group: ResourceGroupUsageData | None  # None when hide_agents=true


@dataclass(frozen=True)
class PresetAvailabilityData:
    """Resource preset with availability information."""

    preset: ResourcePresetData
    available: bool


@dataclass(frozen=True)
class KeypairContextData:
    """Resolved keypair context for a user (access_key + resource_policy)."""

    access_key: AccessKey
    resource_policy: Mapping[str, Any]
