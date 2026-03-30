"""Repository for resource allocation operations."""

from __future__ import annotations

import logging
from collections.abc import Mapping
from typing import Any
from uuid import UUID

from ai.backend.common.types import (
    AccessKey,
    SlotName,
    SlotTypes,
)
from ai.backend.logging.utils import BraceStyleAdapter
from ai.backend.manager.config.provider import ManagerConfigProvider
from ai.backend.manager.data.resource_allocation.types import (
    EffectiveAllocationData,
    KeypairContextData,
    ResourceGroupUsageData,
    ScopeUsageData,
)
from ai.backend.manager.models.utils import ExtendedAsyncSAEngine

from .db_source.db_source import ResourceAllocationDBSource

log = BraceStyleAdapter(logging.getLogger(__spec__.name))


class ResourceAllocationRepository:
    """Repository that wraps the DB source for resource allocation operations."""

    _db_source: ResourceAllocationDBSource
    _config_provider: ManagerConfigProvider

    def __init__(
        self,
        db: ExtendedAsyncSAEngine,
        config_provider: ManagerConfigProvider,
    ) -> None:
        self._db_source = ResourceAllocationDBSource(db)
        self._config_provider = config_provider

    async def get_keypair_context(self, user_id: UUID) -> KeypairContextData:
        """Resolve a user's main keypair context (access_key + resource_policy)."""
        return await self._db_source.get_keypair_context(user_id)

    async def _get_known_slot_types(self) -> Mapping[SlotName, SlotTypes]:
        """Get known slot types from etcd config."""
        return await self._config_provider.legacy_etcd_config_loader.get_resource_slots()

    async def get_keypair_usage(
        self,
        access_key: AccessKey,
        resource_policy: Mapping[str, Any],
    ) -> ScopeUsageData:
        """Get keypair resource usage (limits, used, assignable)."""
        known_slot_types = await self._get_known_slot_types()
        return await self._db_source.get_keypair_usage(
            access_key, resource_policy, known_slot_types
        )

    async def get_project_usage(
        self,
        project_id: UUID,
    ) -> ScopeUsageData:
        """Get project resource usage by project ID (limits, used, assignable)."""
        known_slot_types = await self._get_known_slot_types()
        return await self._db_source.get_project_usage(project_id, known_slot_types)

    async def get_domain_usage(
        self,
        domain_name: str,
    ) -> ScopeUsageData:
        """Get domain resource usage (limits, used, assignable)."""
        known_slot_types = await self._get_known_slot_types()
        return await self._db_source.get_domain_usage(domain_name, known_slot_types)

    async def get_resource_group_usage(
        self,
        rg_name: str,
    ) -> ResourceGroupUsageData:
        """Get resource group (scaling group) usage with max_per_node."""
        known_slot_types = await self._get_known_slot_types()
        return await self._db_source.get_resource_group_usage(rg_name, known_slot_types)

    async def get_effective_allocation(
        self,
        access_key: AccessKey,
        user_id: UUID,
        project_id: UUID,
        domain_name: str,
        resource_policy: Mapping[str, Any],
        rg_name: str,
        group_resource_visibility: bool,
        hide_agents: bool,
        is_admin: bool,
    ) -> EffectiveAllocationData:
        """Compute effective allocation across all scopes."""
        known_slot_types = await self._get_known_slot_types()
        return await self._db_source.get_effective_allocation(
            access_key=access_key,
            user_id=user_id,
            project_id=project_id,
            domain_name=domain_name,
            resource_policy=resource_policy,
            rg_name=rg_name,
            known_slot_types=known_slot_types,
            group_resource_visibility=group_resource_visibility,
            hide_agents=hide_agents,
            is_admin=is_admin,
        )
