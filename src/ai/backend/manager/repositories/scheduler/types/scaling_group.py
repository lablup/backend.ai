"""Scaling group related types."""

from dataclasses import dataclass

from ai.backend.common.identifier.resource_group import ResourceGroupID
from ai.backend.manager.models.scaling_group import ScalingGroupOpts


@dataclass
class ScalingGroupMeta:
    """Scaling group metadata without ORM dependencies."""

    id: ResourceGroupID
    name: str
    scheduler: str
    scheduler_opts: ScalingGroupOpts
