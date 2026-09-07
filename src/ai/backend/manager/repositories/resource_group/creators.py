from __future__ import annotations

from dataclasses import dataclass
from typing import override

from ai.backend.common.data.entity.resource_group import ResourceGroupID
from ai.backend.common.types import AccessKey
from ai.backend.manager.models.resource_group import ResourceGroupForKeypairsRow
from ai.backend.manager.repositories.base.creator import CreatorSpec


@dataclass
class ResourceGroupForKeypairsCreatorSpec(CreatorSpec[ResourceGroupForKeypairsRow]):
    """CreatorSpec for associating a resource group with a keypair."""

    resource_group_id: ResourceGroupID
    access_key: AccessKey

    @override
    def build_row(self) -> ResourceGroupForKeypairsRow:
        return ResourceGroupForKeypairsRow(
            resource_group_id=self.resource_group_id,
            access_key=self.access_key,
        )
