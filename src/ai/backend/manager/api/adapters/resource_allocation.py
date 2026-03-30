"""Resource allocation adapter bridging DTOs and Processors."""

from __future__ import annotations

from collections.abc import Mapping
from typing import Any
from uuid import UUID

from ai.backend.common.contexts.user import current_user
from ai.backend.common.dto.manager.v2.common import (
    BinarySizeInfo,
    ResourceLimitEntryInfo,
    ResourceSlotEntryInfo,
)
from ai.backend.common.dto.manager.v2.resource_allocation.request import (
    AdminEffectiveResourceAllocationInput,
    CheckPresetAvailabilityInput,
    EffectiveResourceAllocationInput,
)
from ai.backend.common.dto.manager.v2.resource_allocation.response import (
    CheckPresetAvailabilityPayload,
    DomainResourceAllocationPayload,
    EffectiveBreakdownNode,
    EffectiveResourceAllocationPayload,
    KeypairResourceAllocationPayload,
    PresetAvailabilityNode,
    ProjectResourceAllocationPayload,
    ResourceGroupResourceAllocationPayload,
    ResourceGroupUsageNode,
    ScopeResourceUsageNode,
)
from ai.backend.common.types import AccessKey, BinarySize, SlotQuantity
from ai.backend.manager.config.provider import ManagerConfigProvider
from ai.backend.manager.data.resource_allocation.types import (
    EffectiveAllocationData,
    PresetAvailabilityData,
    ResourceGroupUsageData,
    ScopeUsageData,
)
from ai.backend.manager.services.processors import Processors
from ai.backend.manager.services.resource_allocation.actions.check_preset_availability import (
    CheckPresetAvailabilityAction,
)
from ai.backend.manager.services.resource_allocation.actions.get_domain_usage import (
    GetDomainUsageAction,
)
from ai.backend.manager.services.resource_allocation.actions.get_effective_allocation import (
    GetEffectiveAllocationAction,
)
from ai.backend.manager.services.resource_allocation.actions.get_keypair_usage import (
    GetKeypairUsageAction,
)
from ai.backend.manager.services.resource_allocation.actions.get_project_usage import (
    GetProjectUsageAction,
)
from ai.backend.manager.services.resource_allocation.actions.get_resource_group_usage import (
    GetResourceGroupUsageAction,
)
from ai.backend.manager.services.resource_allocation.actions.resolve_keypair_context import (
    ResolveKeypairContextAction,
)

from .base import BaseAdapter


def _humanize_bytes(value: int) -> str:
    """Convert bytes integer to human-readable string (e.g., 1073741824 -> '1g')."""
    return f"{BinarySize(value):s}"


def _to_binary_size_info(value: int) -> BinarySizeInfo:
    """Convert bytes integer to BinarySizeInfo DTO."""
    return BinarySizeInfo(value=value, display=_humanize_bytes(value))


class ResourceAllocationAdapter(BaseAdapter):
    """Adapter for resource allocation operations."""

    _config_provider: ManagerConfigProvider | None

    def __init__(
        self,
        processors: Processors,
        config_provider: ManagerConfigProvider | None,
    ) -> None:
        super().__init__(processors)
        self._config_provider = config_provider

    def _visibility_settings(self) -> tuple[bool, bool]:
        """Return (group_resource_visibility, hide_agents) from config."""
        if self._config_provider is None:
            return False, False
        config = self._config_provider.config
        grv = False
        if config.api.resources is not None:
            grv = config.api.resources.group_resource_visibility
        hide = config.manager.hide_agents
        return grv, hide

    async def _resolve_keypair_context(
        self,
        user_id: UUID,
    ) -> tuple[str, Mapping[str, Any]]:
        """Resolve keypair access_key and resource_policy from user_id.

        Used by GQL resolvers where the request context does not carry
        keypair information directly.
        """
        result = (
            await self._processors.resource_allocation.resolve_keypair_context.wait_for_complete(
                ResolveKeypairContextAction(user_id=user_id)
            )
        )
        return str(result.access_key), result.resource_policy

    async def my_keypair_usage_for_current_user(
        self,
    ) -> KeypairResourceAllocationPayload:
        """Get keypair resource usage for the current user.

        Resolves access_key and resource_policy internally from current_user().
        Intended for GQL resolvers where request context lacks keypair info.
        """
        me = current_user()
        if me is None:
            raise PermissionError("Not authenticated")
        access_key, resource_policy = await self._resolve_keypair_context(me.user_id)
        return await self.my_keypair_usage(
            access_key=access_key,
            resource_policy=resource_policy,
        )

    async def effective_allocation_for_current_user(
        self,
        input: EffectiveResourceAllocationInput,
    ) -> EffectiveResourceAllocationPayload:
        """Get effective allocation for the current user.

        Resolves access_key and resource_policy internally from current_user().
        """
        me = current_user()
        if me is None:
            raise PermissionError("Not authenticated")
        access_key, resource_policy = await self._resolve_keypair_context(me.user_id)
        return await self.effective_allocation(
            input=input,
            access_key=access_key,
            resource_policy=resource_policy,
        )

    async def admin_effective_allocation_resolved(
        self,
        input: AdminEffectiveResourceAllocationInput,
    ) -> EffectiveResourceAllocationPayload:
        """Get effective allocation for a specific user (admin only).

        Resolves access_key and resource_policy from the target user_id.
        """
        access_key, resource_policy = await self._resolve_keypair_context(input.user_id)
        return await self.admin_effective_allocation(
            input=input,
            access_key=access_key,
            resource_policy=resource_policy,
        )

    async def check_preset_availability_for_current_user(
        self,
        input: CheckPresetAvailabilityInput,
    ) -> CheckPresetAvailabilityPayload:
        """Check preset availability for the current user.

        Resolves access_key and resource_policy internally from current_user().
        """
        me = current_user()
        if me is None:
            raise PermissionError("Not authenticated")
        access_key, resource_policy = await self._resolve_keypair_context(me.user_id)
        return await self.check_preset_availability(
            input=input,
            access_key=access_key,
            resource_policy=resource_policy,
        )

    async def my_keypair_usage(
        self,
        access_key: str,
        resource_policy: Mapping[str, Any],
    ) -> KeypairResourceAllocationPayload:
        """Get keypair resource usage for the current user."""
        result = await self._processors.resource_allocation.get_keypair_usage.wait_for_complete(
            GetKeypairUsageAction(
                access_key=AccessKey(access_key),
                resource_policy=resource_policy,
            )
        )
        return KeypairResourceAllocationPayload(
            keypair=_scope_usage_to_node(result.usage),
        )

    async def project_usage(
        self,
        project_id: UUID,
    ) -> ProjectResourceAllocationPayload:
        """Get project resource usage."""
        result = await self._processors.resource_allocation.get_project_usage.wait_for_complete(
            GetProjectUsageAction(
                project_id=project_id,
            )
        )
        return ProjectResourceAllocationPayload(
            project=_scope_usage_to_node(result.usage),
        )

    async def admin_domain_usage(
        self,
        domain_name: str,
    ) -> DomainResourceAllocationPayload:
        """Get domain resource usage (admin only)."""
        result = await self._processors.resource_allocation.get_domain_usage.wait_for_complete(
            GetDomainUsageAction(
                domain_name=domain_name,
            )
        )
        return DomainResourceAllocationPayload(
            domain=_scope_usage_to_node(result.usage),
        )

    async def resource_group_usage(
        self,
        rg_name: str,
    ) -> ResourceGroupResourceAllocationPayload:
        """Get resource group usage."""
        result = (
            await self._processors.resource_allocation.get_resource_group_usage.wait_for_complete(
                GetResourceGroupUsageAction(
                    rg_name=rg_name,
                )
            )
        )
        return ResourceGroupResourceAllocationPayload(
            resource_group=_rg_usage_to_node(result.usage),
        )

    async def effective_allocation(
        self,
        input: EffectiveResourceAllocationInput,
        access_key: str,
        resource_policy: Mapping[str, Any],
    ) -> EffectiveResourceAllocationPayload:
        """Get effective allocation for the current user."""
        me = current_user()
        if me is None:
            raise PermissionError("Not authenticated")
        grv, hide = self._visibility_settings()
        result = (
            await self._processors.resource_allocation.get_effective_allocation.wait_for_complete(
                GetEffectiveAllocationAction(
                    access_key=AccessKey(access_key),
                    user_id=me.user_id,
                    project_id=input.project_id,
                    domain_name=me.domain_name,
                    resource_policy=resource_policy,
                    rg_name=input.resource_group_name,
                    group_resource_visibility=grv,
                    hide_agents=hide,
                    is_admin=me.is_admin,
                )
            )
        )
        return _allocation_to_payload(result.allocation)

    async def admin_effective_allocation(
        self,
        input: AdminEffectiveResourceAllocationInput,
        access_key: str,
        resource_policy: Mapping[str, Any],
    ) -> EffectiveResourceAllocationPayload:
        """Get effective allocation for a specific user (admin only)."""
        grv, hide = self._visibility_settings()
        result = (
            await self._processors.resource_allocation.get_effective_allocation.wait_for_complete(
                GetEffectiveAllocationAction(
                    access_key=AccessKey(access_key),
                    user_id=input.user_id,
                    project_id=input.project_id,
                    domain_name="",  # will be resolved from user_id in the repository
                    resource_policy=resource_policy,
                    rg_name=input.resource_group_name,
                    group_resource_visibility=grv,
                    hide_agents=hide,
                    is_admin=True,
                )
            )
        )
        return _allocation_to_payload(result.allocation)

    async def check_preset_availability(
        self,
        input: CheckPresetAvailabilityInput,
        access_key: str,
        resource_policy: Mapping[str, Any],
    ) -> CheckPresetAvailabilityPayload:
        """Check which resource presets are available for session creation."""
        me = current_user()
        if me is None:
            raise PermissionError("Not authenticated")
        grv, hide = self._visibility_settings()
        result = (
            await self._processors.resource_allocation.check_preset_availability.wait_for_complete(
                CheckPresetAvailabilityAction(
                    access_key=AccessKey(access_key),
                    user_id=me.user_id,
                    project_id=input.project_id,
                    domain_name=me.domain_name,
                    resource_policy=resource_policy,
                    rg_name=input.resource_group_name,
                    group_resource_visibility=grv,
                    hide_agents=hide,
                    is_admin=me.is_admin,
                    scaling_group=input.resource_group_name,
                )
            )
        )
        return CheckPresetAvailabilityPayload(
            presets=[_preset_availability_to_node(p) for p in result.presets],
        )


def _slot_quantities_to_entries(quantities: list[SlotQuantity]) -> list[ResourceSlotEntryInfo]:
    """Convert SlotQuantity list to ResourceSlotEntryInfo list.

    Slots with non-finite quantity (Infinity, NaN) are excluded.
    """
    return [
        ResourceSlotEntryInfo(resource_type=sq.slot_name, quantity=sq.quantity)
        for sq in quantities
        if sq.quantity.is_finite()
    ]


def _slot_quantities_to_limit_entries(
    quantities: list[SlotQuantity],
) -> list[ResourceLimitEntryInfo]:
    """Convert SlotQuantity list to ResourceLimitEntryInfo list.

    Infinite quantities are represented as unlimited=True with quantity=None.
    """
    return [
        ResourceLimitEntryInfo(
            resource_type=sq.slot_name,
            quantity=sq.quantity if sq.quantity.is_finite() else None,
            unlimited=not sq.quantity.is_finite(),
        )
        for sq in quantities
    ]


def _scope_usage_to_node(data: ScopeUsageData) -> ScopeResourceUsageNode:
    """Convert ScopeUsageData to ScopeResourceUsageNode DTO."""
    return ScopeResourceUsageNode(
        limits=_slot_quantities_to_limit_entries(data.limits),
        used=_slot_quantities_to_entries(data.used),
        assignable=_slot_quantities_to_limit_entries(data.assignable),
    )


def _rg_usage_to_node(data: ResourceGroupUsageData) -> ResourceGroupUsageNode:
    """Convert ResourceGroupUsageData to ResourceGroupUsageNode DTO."""
    return ResourceGroupUsageNode(
        capacity=_slot_quantities_to_entries(data.capacity),
        used=_slot_quantities_to_entries(data.used),
        free=_slot_quantities_to_entries(data.free),
        max_per_node=_slot_quantities_to_entries(data.max_per_node),
    )


def _allocation_to_payload(
    data: EffectiveAllocationData,
) -> EffectiveResourceAllocationPayload:
    """Convert EffectiveAllocationData to EffectiveResourceAllocationPayload DTO."""
    return EffectiveResourceAllocationPayload(
        assignable=_slot_quantities_to_limit_entries(data.assignable),
        breakdown=EffectiveBreakdownNode(
            keypair=_scope_usage_to_node(data.keypair),
            project=_scope_usage_to_node(data.project) if data.project else None,
            domain=_scope_usage_to_node(data.domain),
            resource_group=_rg_usage_to_node(data.resource_group) if data.resource_group else None,
        ),
    )


def _preset_availability_to_node(data: PresetAvailabilityData) -> PresetAvailabilityNode:
    """Convert PresetAvailabilityData to PresetAvailabilityNode DTO."""
    return PresetAvailabilityNode(
        id=data.preset.id,
        name=data.preset.name,
        resource_slots=[
            ResourceSlotEntryInfo(resource_type=k, quantity=v)
            for k, v in data.preset.resource_slots.items()
        ],
        shared_memory=(
            _to_binary_size_info(data.preset.shared_memory) if data.preset.shared_memory else None
        ),
        resource_group_name=data.preset.scaling_group_name,
        available=data.available,
    )
