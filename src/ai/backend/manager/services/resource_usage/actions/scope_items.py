"""The resource-group scopes a usage bucket read is answered for."""

from __future__ import annotations

import uuid
from abc import ABC, abstractmethod
from dataclasses import dataclass
from typing import override

from ai.backend.common.data.entity.resource_group import RESOURCE_GROUP_SCOPE_TYPE, ResourceGroupID
from ai.backend.common.data.entity.types import ScopeRef
from ai.backend.manager.models.resource_usage_history.scopes import (
    DomainUsageBucketOperationScope,
    ProjectUsageBucketOperationScope,
    UserUsageBucketOperationScope,
)
from ai.backend.manager.models.scopes import OperationScope

__all__ = (
    "DomainUsageBucketScopeItem",
    "ProjectUsageBucketScopeItem",
    "UsageBucketScopeItem",
    "UserUsageBucketScopeItem",
)


class UsageBucketScopeItem(ABC):
    """One resource group a usage bucket read is answered for.

    The scope the read is authorized against and the rows it is restricted to name
    the same resource group id, so a read cannot be authorized for one and served
    another.
    """

    resource_group_id: ResourceGroupID

    def scope_ref(self) -> ScopeRef:
        return ScopeRef(scope_type=RESOURCE_GROUP_SCOPE_TYPE, scope_id=self.resource_group_id)

    @abstractmethod
    def operation_scope(self) -> OperationScope:
        """The rows the read is restricted to."""
        raise NotImplementedError


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
