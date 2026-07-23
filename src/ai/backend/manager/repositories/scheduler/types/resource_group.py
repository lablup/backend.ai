"""Repository-internal resource group fetch types."""

from dataclasses import dataclass

from ai.backend.manager.views.sokovan.resource_group import ResourceGroupMeta
from ai.backend.manager.views.sokovan.snapshot import ResourceGroupSchedulingPolicy


@dataclass(frozen=True)
class ResourceGroupFetch:
    """DB-derived resource group data: identity plus scheduling policy."""

    meta: ResourceGroupMeta
    policy: ResourceGroupSchedulingPolicy
