"""The resource-group scopes a usage bucket read is answered for."""

from __future__ import annotations

import uuid
from abc import ABC
from dataclasses import dataclass
from typing import override

from ai.backend.common.data.entity.resource_group import ResourceGroupID
from ai.backend.common.data.entity.types import EntityIdentifier
from ai.backend.manager.actions.v2.ops.base import ScopeItem
from ai.backend.manager.models.resource_usage_history.scopes import (
    DomainUsageBucketOperationScope,
    ProjectUsageBucketOperationScope,
    UserUsageBucketOperationScope,
)

__all__ = (
    "DomainUsageBucketScopeItem",
    "ProjectUsageBucketScopeItem",
    "UsageBucketScopeItem",
    "UserUsageBucketScopeItem",
)


class UsageBucketScopeItem(ScopeItem, ABC):
    """One resource group a usage bucket read is answered for.

    Both sides name the same resource group id, so the scope is read off the item
    rather than declared per kind.
    """

    resource_group_id: ResourceGroupID

    @override
    def scope_ref(self) -> EntityIdentifier:
        return self.resource_group_id


@dataclass(frozen=True)
class DomainUsageBucketScopeItem(UsageBucketScopeItem):
    """The domain usage buckets of one resource group."""

    resource_group_id: ResourceGroupID
    domain_name: str

    @override
    def operation_scope(self) -> DomainUsageBucketOperationScope:
        return DomainUsageBucketOperationScope(
            resource_group_id=self.resource_group_id,
            domain_name=self.domain_name,
        )


@dataclass(frozen=True)
class ProjectUsageBucketScopeItem(UsageBucketScopeItem):
    """The project usage buckets of one resource group."""

    resource_group_id: ResourceGroupID
    domain_name: str
    project_id: uuid.UUID

    @override
    def operation_scope(self) -> ProjectUsageBucketOperationScope:
        return ProjectUsageBucketOperationScope(
            resource_group_id=self.resource_group_id,
            domain_name=self.domain_name,
            project_id=self.project_id,
        )


@dataclass(frozen=True)
class UserUsageBucketScopeItem(UsageBucketScopeItem):
    """The user usage buckets of one resource group."""

    resource_group_id: ResourceGroupID
    domain_name: str
    project_id: uuid.UUID
    user_uuid: uuid.UUID

    @override
    def operation_scope(self) -> UserUsageBucketOperationScope:
        return UserUsageBucketOperationScope(
            resource_group_id=self.resource_group_id,
            domain_name=self.domain_name,
            project_id=self.project_id,
            user_uuid=self.user_uuid,
        )
