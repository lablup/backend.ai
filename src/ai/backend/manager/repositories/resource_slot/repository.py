"""Resource Slot Repository with Resilience policies."""

from __future__ import annotations

import uuid
from decimal import Decimal
from typing import TYPE_CHECKING

from ai.backend.common.metrics.metric import DomainType, LayerType
from ai.backend.common.resilience import (
    MetricArgs,
    MetricPolicy,
    Resilience,
    RetryArgs,
    RetryPolicy,
)
from ai.backend.common.resilience.policies.retry import BackoffStrategy
from ai.backend.manager.data.resource_slot.types import (
    AgentResourceDrift,
    AgentResourceSearchResult,
    ResourceAllocationSearchResult,
    ResourceOccupancy,
    ResourceSlotTypeSearchResult,
)
from ai.backend.manager.models.resource_slot import (
    AgentResourceRow,
    ResourceAllocationRow,
    ResourceSlotTypeRow,
)
from ai.backend.manager.repositories.base import BatchQuerier

from .db_source import ResourceSlotDBSource

if TYPE_CHECKING:
    from ai.backend.manager.models.utils import ExtendedAsyncSAEngine

__all__ = ("ResourceSlotRepository",)


resource_slot_repository_resilience = Resilience(
    policies=[
        MetricPolicy(
            MetricArgs(domain=DomainType.REPOSITORY, layer=LayerType.RESOURCE_SLOT_REPOSITORY)
        ),
        RetryPolicy(
            RetryArgs(
                max_retries=10,
                retry_delay=0.1,
                backoff_strategy=BackoffStrategy.FIXED,
            )
        ),
    ]
)


class ResourceSlotRepository:
    """Repository for normalized resource slot data access with resilience policies.

    Manages three tables:
    - resource_slot_types: Registry of known slot types
    - agent_resources: Per-agent, per-slot capacity and usage
    - resource_allocations: Per-kernel, per-slot resource allocation
    """

    _db_source: ResourceSlotDBSource

    def __init__(self, db: ExtendedAsyncSAEngine) -> None:
        self._db_source = ResourceSlotDBSource(db)

    # ==================== resource_slot_types ====================

    @resource_slot_repository_resilience.apply()
    async def all_slot_types(self) -> list[ResourceSlotTypeRow]:
        """List all registered resource slot types."""
        return await self._db_source.all_slot_types()

    @resource_slot_repository_resilience.apply()
    async def get_slot_type(self, slot_name: str) -> ResourceSlotTypeRow:
        """Get a specific resource slot type by name."""
        return await self._db_source.get_slot_type(slot_name)

    @resource_slot_repository_resilience.apply()
    async def search_slot_types(self, querier: BatchQuerier) -> ResourceSlotTypeSearchResult:
        """Paginated search across resource slot types."""
        return await self._db_source.search_slot_types(querier)

    # ==================== agent_resources ====================

    @resource_slot_repository_resilience.apply()
    async def get_agent_resources(self, agent_id: str) -> list[AgentResourceRow]:
        """Get all slot capacity/usage rows for a given agent."""
        return await self._db_source.get_agent_resources(agent_id)

    @resource_slot_repository_resilience.apply()
    async def get_agent_resource_by_slot(self, agent_id: str, slot_name: str) -> AgentResourceRow:
        """Get a single slot row for one agent+slot combination."""
        return await self._db_source.get_agent_resource_by_slot(agent_id, slot_name)

    @resource_slot_repository_resilience.apply()
    async def search_agent_resources(self, querier: BatchQuerier) -> AgentResourceSearchResult:
        return await self._db_source.search_agent_resources(querier)

    # ==================== resource_allocations ====================

    @resource_slot_repository_resilience.apply()
    async def get_kernel_allocations(self, kernel_id: uuid.UUID) -> list[ResourceAllocationRow]:
        """Get all per-slot allocation rows for a given kernel."""
        return await self._db_source.get_kernel_allocations(kernel_id)

    @resource_slot_repository_resilience.apply()
    async def get_kernel_allocation_by_slot(
        self, kernel_id: uuid.UUID, slot_name: str
    ) -> ResourceAllocationRow:
        """Get a single allocation row for one kernel+slot combination."""
        return await self._db_source.get_kernel_allocation_by_slot(kernel_id, slot_name)

    @resource_slot_repository_resilience.apply()
    async def search_resource_allocations(
        self, querier: BatchQuerier
    ) -> ResourceAllocationSearchResult:
        return await self._db_source.search_resource_allocations(querier)

    # ==================== Aggregation ====================

    @resource_slot_repository_resilience.apply()
    async def compute_actual_agent_resource_usage(
        self,
    ) -> dict[tuple[str, str], Decimal]:
        """Compute actual per-agent per-slot resource usage from active allocations."""
        return await self._db_source.compute_actual_agent_resource_usage()

    @resource_slot_repository_resilience.apply()
    async def reconcile_agent_resources(self) -> list[AgentResourceDrift]:
        """Compare agent_resources.used against actual allocations and correct drift."""
        return await self._db_source.reconcile_agent_resources()

    @resource_slot_repository_resilience.apply()
    async def get_domain_resource_overview(self, domain_name: str) -> ResourceOccupancy:
        """Get aggregated active resource occupancy for a domain."""
        return await self._db_source.aggregate_occupied_by_domain(domain_name)

    @resource_slot_repository_resilience.apply()
    async def get_project_resource_overview(self, project_id: uuid.UUID) -> ResourceOccupancy:
        """Get aggregated active resource occupancy for a project (group)."""
        return await self._db_source.aggregate_occupied_by_project(project_id)
