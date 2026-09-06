from __future__ import annotations

from dataclasses import dataclass
from typing import override
from uuid import UUID

from ai.backend.common.data.entity.domain import DomainID
from ai.backend.common.data.entity.resource_group import ResourceGroupID
from ai.backend.common.types import AccessKey
from ai.backend.manager.models.resource_group import (
    ResourceGroupForDomainRow,
    ResourceGroupForKeypairsRow,
    ResourceGroupForProjectRow,
)
from ai.backend.manager.repositories.base.creator import CreatorSpec


@dataclass
class ResourceGroupForDomainCreatorSpec(CreatorSpec[ResourceGroupForDomainRow]):
    """CreatorSpec for associating a resource group with a domain."""

    resource_group_id: ResourceGroupID
    domain_id: DomainID

    @override
    def build_row(self) -> ResourceGroupForDomainRow:
        return ResourceGroupForDomainRow(
            resource_group_id=self.resource_group_id,
            domain_id=self.domain_id,
        )


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


@dataclass
class ResourceGroupForProjectCreatorSpec(CreatorSpec[ResourceGroupForProjectRow]):
    """CreatorSpec for associating a resource group with a project (user group)."""

    resource_group_id: ResourceGroupID
    project: UUID

    @override
    def build_row(self) -> ResourceGroupForProjectRow:
        return ResourceGroupForProjectRow(
            resource_group_id=self.resource_group_id,
            group=self.project,
        )
