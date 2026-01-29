"""Actions and results for Resource Usage Service."""

from __future__ import annotations

from dataclasses import dataclass
from typing import override

from ai.backend.manager.actions.action import BaseAction, BaseActionResult
from ai.backend.manager.repositories.base import QueryCondition, QueryOrder, QueryPagination
from ai.backend.manager.repositories.resource_usage_history import (
    DomainUsageBucketData,
    ProjectUsageBucketData,
    UserUsageBucketData,
)

# Domain Usage Buckets


@dataclass
class DomainUsageBucketAction(BaseAction):
    """Base action for domain usage bucket operations."""

    @override
    @classmethod
    def entity_type(cls) -> str:
        return "domain_usage_bucket"


@dataclass
class SearchDomainUsageBucketsAction(DomainUsageBucketAction):
    """Action to search domain usage buckets."""

    pagination: QueryPagination
    conditions: list[QueryCondition]
    orders: list[QueryOrder]

    @override
    @classmethod
    def operation_type(cls) -> str:
        return "search"

    @override
    def entity_id(self) -> str | None:
        return None


@dataclass
class SearchDomainUsageBucketsActionResult(BaseActionResult):
    """Result of searching domain usage buckets."""

    items: list[DomainUsageBucketData]
    total_count: int

    @override
    def entity_id(self) -> str | None:
        return None


# Project Usage Buckets


@dataclass
class ProjectUsageBucketAction(BaseAction):
    """Base action for project usage bucket operations."""

    @override
    @classmethod
    def entity_type(cls) -> str:
        return "project_usage_bucket"


@dataclass
class SearchProjectUsageBucketsAction(ProjectUsageBucketAction):
    """Action to search project usage buckets."""

    pagination: QueryPagination
    conditions: list[QueryCondition]
    orders: list[QueryOrder]

    @override
    @classmethod
    def operation_type(cls) -> str:
        return "search"

    @override
    def entity_id(self) -> str | None:
        return None


@dataclass
class SearchProjectUsageBucketsActionResult(BaseActionResult):
    """Result of searching project usage buckets."""

    items: list[ProjectUsageBucketData]
    total_count: int

    @override
    def entity_id(self) -> str | None:
        return None


# User Usage Buckets


@dataclass
class UserUsageBucketAction(BaseAction):
    """Base action for user usage bucket operations."""

    @override
    @classmethod
    def entity_type(cls) -> str:
        return "user_usage_bucket"


@dataclass
class SearchUserUsageBucketsAction(UserUsageBucketAction):
    """Action to search user usage buckets."""

    pagination: QueryPagination
    conditions: list[QueryCondition]
    orders: list[QueryOrder]

    @override
    @classmethod
    def operation_type(cls) -> str:
        return "search"

    @override
    def entity_id(self) -> str | None:
        return None


@dataclass
class SearchUserUsageBucketsActionResult(BaseActionResult):
    """Result of searching user usage buckets."""

    items: list[UserUsageBucketData]
    total_count: int

    @override
    def entity_id(self) -> str | None:
        return None
