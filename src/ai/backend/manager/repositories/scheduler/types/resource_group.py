"""Repository-internal resource group fetch types."""

from collections.abc import Mapping
from dataclasses import dataclass
from decimal import Decimal

from ai.backend.common.data.entity.resource_slot import ResourceSlotName
from ai.backend.common.schema.resource_group import PreemptionConfig
from ai.backend.manager.views.sokovan.resource_group import ResourceGroupMeta
from ai.backend.manager.views.sokovan.snapshot import ResourceGroupSchedulingPolicy


@dataclass(frozen=True)
class ResourceGroupFetch:
    """DB-derived resource group data: identity plus scheduling policy."""

    meta: ResourceGroupMeta
    policy: ResourceGroupSchedulingPolicy
    preemption: PreemptionConfig
    # Node shapes of the compute cluster of a `kubernetes` group; None otherwise
    node_shapes: tuple[Mapping[ResourceSlotName, Decimal], ...] | None = None
