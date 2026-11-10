from __future__ import annotations

from collections.abc import Sequence
from typing import override

from pydantic import Field

from ai.backend.common.data.entity.domain import DomainID
from ai.backend.common.data.entity.project import ProjectID
from ai.backend.common.data.entity.resource_group import ResourceGroupID
from ai.backend.common.data.entity.user import UserID
from ai.backend.common.types import AccessKey
from ai.backend.manager.models.resource_group.creators import (
    ResourceGroupForDomainRelationCreator,
    ResourceGroupForKeypairRelationCreator,
    ResourceGroupForProjectRelationCreator,
)
from ai.backend.manager.repositories.ops.v2.seed.types import SeedRelationWrite
from ai.backend.manager.seed.base import SeedItems, SeedRejection, SeedRelationItem


class ResourceGroupForDomainSeed(SeedRelationItem):
    """One ``sgroups_for_domains`` row: a resource group allowed to a domain."""

    domain_id: DomainID
    resource_group_id: ResourceGroupID

    @override
    def key(self) -> str:
        return f"{self.domain_id}:{self.resource_group_id}"

    @override
    def write(self) -> SeedRelationWrite:
        return SeedRelationWrite(
            creator=ResourceGroupForDomainRelationCreator(),
            scope=self.domain_id,
            target=self.resource_group_id,
        )

    @override
    def check(self) -> list[str]:
        return []

    @override
    @classmethod
    def reject(cls, files: Sequence[SeedItems[ResourceGroupForDomainSeed]]) -> list[SeedRejection]:
        """None: an item naming a missing domain or resource group fails when written."""
        return []


class ResourceGroupForProjectSeed(SeedRelationItem):
    """One ``sgroups_for_groups`` row: a resource group allowed to a project."""

    project_id: ProjectID
    resource_group_id: ResourceGroupID

    @override
    def key(self) -> str:
        return f"{self.project_id}:{self.resource_group_id}"

    @override
    def write(self) -> SeedRelationWrite:
        return SeedRelationWrite(
            creator=ResourceGroupForProjectRelationCreator(),
            scope=self.project_id,
            target=self.resource_group_id,
        )

    @override
    def check(self) -> list[str]:
        return []

    @override
    @classmethod
    def reject(cls, files: Sequence[SeedItems[ResourceGroupForProjectSeed]]) -> list[SeedRejection]:
        """None: an item naming a missing project or resource group fails when written."""
        return []


class ResourceGroupForKeypairSeed(SeedRelationItem):
    """One ``sgroups_for_keypairs`` row: a resource group allowed to a keypair. The graph
    links the keypair's owner, which the item names; a key the owner does not hold fails."""

    access_key: AccessKey = Field(min_length=1, max_length=20)
    user_id: UserID
    resource_group_id: ResourceGroupID

    @override
    def key(self) -> str:
        return f"{self.access_key}:{self.resource_group_id}"

    @override
    def write(self) -> SeedRelationWrite:
        return SeedRelationWrite(
            creator=ResourceGroupForKeypairRelationCreator(access_key=self.access_key),
            scope=self.user_id,
            target=self.resource_group_id,
        )

    @override
    def check(self) -> list[str]:
        return []

    @override
    @classmethod
    def reject(cls, files: Sequence[SeedItems[ResourceGroupForKeypairSeed]]) -> list[SeedRejection]:
        """None: an item naming a missing keypair, user or resource group fails when
        written."""
        return []
