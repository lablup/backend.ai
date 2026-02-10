"""Resource Slot Repository with Resilience policies."""

from __future__ import annotations

from collections.abc import Sequence
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
from ai.backend.common.types import AgentId, SlotQuantity
from ai.backend.manager.models.resource_slot import ResourceSlotTypeRow
from ai.backend.manager.repositories.base import (
    BulkUpserter,
)

from .db_source import ResourceSlotDBSource
from .types import AgentOccupiedSlots

if TYPE_CHECKING:
    import uuid

    from ai.backend.manager.models.resource_slot import (
        AgentResourceRow,
    )
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

    # ==================== resource_allocations ====================

    @resource_slot_repository_resilience.apply()
    async def request_resources(
        self,
        kernel_id: uuid.UUID,
        slots: Sequence[SlotQuantity],
    ) -> int:
        """INSERT allocation rows with requested amounts only."""
        return await self._db_source.request_resources(kernel_id, slots)

    # ==================== resource_allocations + agent_resources ====================

    @resource_slot_repository_resilience.apply()
    async def allocate_resources(
        self,
        kernel_id: uuid.UUID,
        agent_id: str,
        slots: Sequence[SlotQuantity],
    ) -> int:
        """Set used values on allocations + increment agent_resources.used."""
        return await self._db_source.allocate_resources(kernel_id, agent_id, slots)

    @resource_slot_repository_resilience.apply()
    async def free_resources(
        self,
        kernel_id: uuid.UUID,
        agent_id: str,
    ) -> int:
        """Set free_at on allocations + decrement agent_resources.used."""
        return await self._db_source.free_resources(kernel_id, agent_id)

    # ==================== agent_resources ====================

    @resource_slot_repository_resilience.apply()
    async def upsert_agent_capacity(
        self,
        bulk_upserter: BulkUpserter[AgentResourceRow],
    ) -> int:
        """Bulk UPSERT agent resource capacity rows."""
        return await self._db_source.upsert_agent_capacity(bulk_upserter)

    # ==================== SQL Aggregation Queries ====================

    @resource_slot_repository_resilience.apply()
    async def get_agent_occupancy(
        self,
        agent_ids: set[AgentId],
    ) -> list[AgentOccupiedSlots]:
        """Calculate current occupied slots for given agents."""
        return await self._db_source.get_agent_occupancy(agent_ids)

    # ==================== resource_slot_types ====================

    @resource_slot_repository_resilience.apply()
    async def all_slot_types(self) -> list[ResourceSlotTypeRow]:
        """List all registered resource slot types."""
        return await self._db_source.all_slot_types()

    @resource_slot_repository_resilience.apply()
    async def get_slot_type(self, slot_name: str) -> ResourceSlotTypeRow:
        """Get a specific resource slot type by name."""
        return await self._db_source.get_slot_type(slot_name)
