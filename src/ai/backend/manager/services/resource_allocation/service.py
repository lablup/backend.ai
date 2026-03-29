"""Service for resource allocation operations."""

from __future__ import annotations

import logging

from ai.backend.logging.utils import BraceStyleAdapter
from ai.backend.manager.data.resource_allocation.types import PresetAvailabilityData
from ai.backend.manager.repositories.resource_allocation.repository import (
    ResourceAllocationRepository,
)
from ai.backend.manager.repositories.resource_preset.repository import ResourcePresetRepository
from ai.backend.manager.repositories.resource_slot.types import (
    quantities_ge,
    resource_slot_to_quantities,
)
from ai.backend.manager.services.resource_allocation.actions.check_preset_availability import (
    CheckPresetAvailabilityAction,
    CheckPresetAvailabilityActionResult,
)
from ai.backend.manager.services.resource_allocation.actions.get_domain_usage import (
    GetDomainUsageAction,
    GetDomainUsageActionResult,
)
from ai.backend.manager.services.resource_allocation.actions.get_effective_allocation import (
    GetEffectiveAllocationAction,
    GetEffectiveAllocationActionResult,
)
from ai.backend.manager.services.resource_allocation.actions.get_keypair_usage import (
    GetKeypairUsageAction,
    GetKeypairUsageActionResult,
)
from ai.backend.manager.services.resource_allocation.actions.get_project_usage import (
    GetProjectUsageAction,
    GetProjectUsageActionResult,
)
from ai.backend.manager.services.resource_allocation.actions.get_resource_group_usage import (
    GetResourceGroupUsageAction,
    GetResourceGroupUsageActionResult,
)
from ai.backend.manager.services.resource_allocation.actions.resolve_keypair_context import (
    ResolveKeypairContextAction,
    ResolveKeypairContextActionResult,
)

log = BraceStyleAdapter(logging.getLogger(__spec__.name))


class ResourceAllocationService:
    """Service for resource allocation operations."""

    _resource_allocation_repository: ResourceAllocationRepository
    _resource_preset_repository: ResourcePresetRepository

    def __init__(
        self,
        resource_allocation_repository: ResourceAllocationRepository,
        resource_preset_repository: ResourcePresetRepository,
    ) -> None:
        self._resource_allocation_repository = resource_allocation_repository
        self._resource_preset_repository = resource_preset_repository

    async def resolve_keypair_context(
        self, action: ResolveKeypairContextAction
    ) -> ResolveKeypairContextActionResult:
        """Resolve a user's main keypair context (access_key + resource_policy)."""
        ctx = await self._resource_allocation_repository.get_keypair_context(
            user_id=action.user_id,
        )
        return ResolveKeypairContextActionResult(
            access_key=ctx.access_key,
            resource_policy=ctx.resource_policy,
        )

    async def get_keypair_usage(self, action: GetKeypairUsageAction) -> GetKeypairUsageActionResult:
        """Get keypair resource usage."""
        usage = await self._resource_allocation_repository.get_keypair_usage(
            access_key=action.access_key,
            resource_policy=action.resource_policy,
        )
        return GetKeypairUsageActionResult(usage=usage)

    async def get_project_usage(self, action: GetProjectUsageAction) -> GetProjectUsageActionResult:
        """Get project resource usage."""
        usage = await self._resource_allocation_repository.get_project_usage(
            project_id=action.project_id,
        )
        return GetProjectUsageActionResult(usage=usage)

    async def get_domain_usage(self, action: GetDomainUsageAction) -> GetDomainUsageActionResult:
        """Get domain resource usage."""
        usage = await self._resource_allocation_repository.get_domain_usage(
            domain_name=action.domain_name,
        )
        return GetDomainUsageActionResult(usage=usage)

    async def get_resource_group_usage(
        self, action: GetResourceGroupUsageAction
    ) -> GetResourceGroupUsageActionResult:
        """Get resource group usage."""
        usage = await self._resource_allocation_repository.get_resource_group_usage(
            rg_name=action.rg_name,
        )
        return GetResourceGroupUsageActionResult(usage=usage)

    async def get_effective_allocation(
        self, action: GetEffectiveAllocationAction
    ) -> GetEffectiveAllocationActionResult:
        """Get effective allocation across all scopes."""
        allocation = await self._resource_allocation_repository.get_effective_allocation(
            access_key=action.access_key,
            user_id=action.user_id,
            project_id=action.project_id,
            domain_name=action.domain_name,
            resource_policy=action.resource_policy,
            rg_name=action.rg_name,
            group_resource_visibility=action.group_resource_visibility,
            hide_agents=action.hide_agents,
            is_admin=action.is_admin,
        )
        return GetEffectiveAllocationActionResult(allocation=allocation)

    async def check_preset_availability(
        self, action: CheckPresetAvailabilityAction
    ) -> CheckPresetAvailabilityActionResult:
        """Check which presets are allocatable given current resource state.

        1. Get effective allocation data
        2. Get preset list from resource_preset repository
        3. For each preset: check if preset_slots <= effective_assignable
           AND preset_slots <= max_per_node
        4. Return list of PresetAvailabilityData
        """
        allocation = await self._resource_allocation_repository.get_effective_allocation(
            access_key=action.access_key,
            user_id=action.user_id,
            project_id=action.project_id,
            domain_name=action.domain_name,
            resource_policy=action.resource_policy,
            rg_name=action.rg_name,
            group_resource_visibility=action.group_resource_visibility,
            hide_agents=action.hide_agents,
            is_admin=action.is_admin,
        )

        preset_data_list = await self._resource_preset_repository.list_presets(
            action.scaling_group,
        )

        presets: list[PresetAvailabilityData] = []
        for preset_data in preset_data_list:
            preset_slots = resource_slot_to_quantities(
                preset_data.resource_slots.normalize_slots(ignore_unknown=True)
            )
            allocatable = quantities_ge(allocation.assignable, preset_slots)
            # Also check max_per_node if resource group data is available
            if allocatable and allocation.resource_group is not None:
                allocatable = quantities_ge(allocation.resource_group.max_per_node, preset_slots)

            presets.append(
                PresetAvailabilityData(
                    preset=preset_data,
                    available=allocatable,
                )
            )

        return CheckPresetAvailabilityActionResult(presets=presets)
