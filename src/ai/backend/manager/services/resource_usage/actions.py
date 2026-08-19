"""Actions and results for Resource Usage Service."""

from __future__ import annotations

from dataclasses import dataclass
from typing import override

from ai.backend.common.data.permission.types import EntityType
from ai.backend.manager.actions.action import BaseAction, BaseActionResult
from ai.backend.manager.actions.types import ActionOperationType
from ai.backend.manager.models.clauses import QueryCondition, QueryOrder
from ai.backend.manager.models.specs.pagination import QueryPagination
from ai.backend.manager.repositories.base import BatchQuerier
from ai.backend.manager.repositories.resource_usage_history import (
    DomainUsageBucketData,
    DomainUsageBucketOperationScope,
    ProjectUsageBucketData,
    ProjectUsageBucketOperationScope,
    UserUsageBucketData,
    UserUsageBucketOperationScope,
)

# Domain Usage Buckets


@dataclass
class DomainUsageBucketAction(BaseAction):
    """Base action for domain usage bucket operations."""

    @override
    @classmethod
    def entity_type(cls) -> EntityType:
        return EntityType.DOMAIN_USAGE_BUCKET


@dataclass
class SearchDomainUsageBucketsAction(DomainUsageBucketAction):
    """Action to search domain usage buckets."""

    pagination: QueryPagination
    conditions: list[QueryCondition]
    orders: list[QueryOrder]

    @override
    @classmethod
    def operation_type(cls) -> ActionOperationType:
        return ActionOperationType.SEARCH

    @override
    def entity_id(self) -> str | None:
        return None


@dataclass
class SearchDomainUsageBucketsActionResult(BaseActionResult):
    """Result of searching domain usage buckets."""

    items: list[DomainUsageBucketData]
    total_count: int
    has_next_page: bool
    has_previous_page: bool

    @override
    def entity_id(self) -> str | None:
        return None


# Project Usage Buckets


@dataclass
class ProjectUsageBucketAction(BaseAction):
    """Base action for project usage bucket operations."""

    @override
    @classmethod
    def entity_type(cls) -> EntityType:
        return EntityType.PROJECT_USAGE_BUCKET


@dataclass
class SearchProjectUsageBucketsAction(ProjectUsageBucketAction):
    """Action to search project usage buckets."""

    pagination: QueryPagination
    conditions: list[QueryCondition]
    orders: list[QueryOrder]

    @override
    @classmethod
    def operation_type(cls) -> ActionOperationType:
        return ActionOperationType.SEARCH

    @override
    def entity_id(self) -> str | None:
        return None


@dataclass
class SearchProjectUsageBucketsActionResult(BaseActionResult):
    """Result of searching project usage buckets."""

    items: list[ProjectUsageBucketData]
    total_count: int
    has_next_page: bool
    has_previous_page: bool

    @override
    def entity_id(self) -> str | None:
        return None


# User Usage Buckets


@dataclass
class UserUsageBucketAction(BaseAction):
    """Base action for user usage bucket operations."""

    @override
    @classmethod
    def entity_type(cls) -> EntityType:
        return EntityType.USER_USAGE_BUCKET


@dataclass
class SearchUserUsageBucketsAction(UserUsageBucketAction):
    """Action to search user usage buckets."""

    pagination: QueryPagination
    conditions: list[QueryCondition]
    orders: list[QueryOrder]

    @override
    @classmethod
    def operation_type(cls) -> ActionOperationType:
        return ActionOperationType.SEARCH

    @override
    def entity_id(self) -> str | None:
        return None


@dataclass
class SearchUserUsageBucketsActionResult(BaseActionResult):
    """Result of searching user usage buckets."""

    items: list[UserUsageBucketData]
    total_count: int
    has_next_page: bool
    has_previous_page: bool

    @override
    def entity_id(self) -> str | None:
        return None


# Scoped Usage Bucket Actions


@dataclass
class OperationScopedDomainUsageBucketsAction(DomainUsageBucketAction):
    """Search domain usage buckets within scope."""

    scope: DomainUsageBucketOperationScope
    querier: BatchQuerier

    @override
    @classmethod
    def operation_type(cls) -> ActionOperationType:
        return ActionOperationType.SEARCH

    @override
    def entity_id(self) -> str | None:
        return f"{self.scope.resource_group}:{self.scope.domain_name}"


@dataclass
class OperationScopedDomainUsageBucketsActionResult(BaseActionResult):
    """Result of scoped domain usage bucket search."""

    items: list[DomainUsageBucketData]
    total_count: int
    has_next_page: bool
    has_previous_page: bool

    @override
    def entity_id(self) -> str | None:
        return None


@dataclass
class OperationScopedProjectUsageBucketsAction(ProjectUsageBucketAction):
    """Search project usage buckets within scope."""

    scope: ProjectUsageBucketOperationScope
    querier: BatchQuerier

    @override
    @classmethod
    def operation_type(cls) -> ActionOperationType:
        return ActionOperationType.SEARCH

    @override
    def entity_id(self) -> str | None:
        return f"{self.scope.resource_group}:{self.scope.domain_name}:{self.scope.project_id}"


@dataclass
class OperationScopedProjectUsageBucketsActionResult(BaseActionResult):
    """Result of scoped project usage bucket search."""

    items: list[ProjectUsageBucketData]
    total_count: int
    has_next_page: bool
    has_previous_page: bool

    @override
    def entity_id(self) -> str | None:
        return None


@dataclass
class OperationScopedUserUsageBucketsAction(UserUsageBucketAction):
    """Search user usage buckets within scope."""

    scope: UserUsageBucketOperationScope
    querier: BatchQuerier

    @override
    @classmethod
    def operation_type(cls) -> ActionOperationType:
        return ActionOperationType.SEARCH

    @override
    def entity_id(self) -> str | None:
        return f"{self.scope.resource_group}:{self.scope.domain_name}:{self.scope.project_id}:{self.scope.user_uuid}"


@dataclass
class OperationScopedUserUsageBucketsActionResult(BaseActionResult):
    """Result of scoped user usage bucket search."""

    items: list[UserUsageBucketData]
    total_count: int
    has_next_page: bool
    has_previous_page: bool

    @override
    def entity_id(self) -> str | None:
        return None
