"""Resource Slot Repository with Resilience policies."""

from __future__ import annotations

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
from ai.backend.manager.models.resource_slot import ResourceSlotTypeRow

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
