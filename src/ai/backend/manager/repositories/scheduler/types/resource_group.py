"""Resource group related types."""

from dataclasses import dataclass

from ai.backend.common.identifier.resource_group import ResourceGroupID, ResourceGroupName
from ai.backend.manager.models.scaling_group import ScalingGroupOpts


@dataclass
class ResourceGroupMeta:
    """Resource group metadata without ORM dependencies."""

    id: ResourceGroupID
    name: ResourceGroupName
    scheduler: str
    scheduler_opts: ScalingGroupOpts
