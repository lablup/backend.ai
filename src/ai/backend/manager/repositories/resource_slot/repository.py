"""Resource Slot Repository with Resilience policies."""

from __future__ import annotations

import uuid
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
    AgentResourceSearchResult,
    ResourceAllocationSearchResult,
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

    # ==================== agent_resources ====================

    @resource_slot_repository_resilience.apply()
    async def get_agent_resources(self, agent_id: str) -> list[AgentResourceRow]:
        """Get all slot capacity/usage rows for a given agent."""
        return await self._db_source.get_agent_resources(agent_id)

    @resource_slot_repository_resilience.apply()
    async def search_agent_resources(self, querier: BatchQuerier) -> AgentResourceSearchResult:
        return await self._db_source.search_agent_resources(querier)

    # ==================== resource_allocations ====================

    @resource_slot_repository_resilience.apply()
    async def get_kernel_allocations(self, kernel_id: uuid.UUID) -> list[ResourceAllocationRow]:
        """Get all per-slot allocation rows for a given kernel."""
        return await self._db_source.get_kernel_allocations(kernel_id)

    @resource_slot_repository_resilience.apply()
    async def search_resource_allocations(
        self, querier: BatchQuerier
    ) -> ResourceAllocationSearchResult:
        return await self._db_source.search_resource_allocations(querier)
