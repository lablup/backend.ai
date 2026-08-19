"""Resource group related view types."""

from dataclasses import dataclass

from ai.backend.common.identifier.resource_group import ResourceGroupID, ResourceGroupName


@dataclass
class ResourceGroupMeta:
    """Resource group identity without ORM dependencies."""

    id: ResourceGroupID
    name: ResourceGroupName
