from __future__ import annotations

from abc import ABC, abstractmethod
from dataclasses import dataclass
from typing import TYPE_CHECKING

import strawberry

from ai.backend.common.dto.manager.v2.fair_share.types import (
    DomainUsageBucketScopeDTO,
    ProjectUsageBucketScopeDTO,
    ResourceGroupDomainScopeDTO,
    ResourceGroupProjectScopeDTO,
    ResourceGroupUserScopeDTO,
    UserUsageBucketScopeDTO,
)
from ai.backend.manager.api.gql.data_loader.data_loaders import DataLoaders
from ai.backend.manager.config.provider import ManagerConfigProvider
from ai.backend.manager.repositories.base import QueryCondition, QueryOrder

if TYPE_CHECKING:
    from ai.backend.common.events.fetcher import EventFetcher
    from ai.backend.common.events.hub.hub import EventHub
    from ai.backend.common.metrics.metric import GraphQLMetricObserver
    from ai.backend.manager.api.adapters.registry import Adapters
    from ai.backend.manager.api.gql.adapter import BaseGQLAdapter
    from ai.backend.manager.services.processors import Processors  # pants: no-infer-dep


class GQLFilter(ABC):
    """Abstract base class for GraphQL filter types.

    All GraphQL filter input types should inherit from this ABC
    to ensure they implement the build_conditions method.
    """

    @abstractmethod
    def build_conditions(self) -> list[QueryCondition]:
        """Build query conditions from this filter.

        Returns:
            A list of QueryCondition callables that can be applied to SQLAlchemy queries.
        """
        raise NotImplementedError


class GQLOrderBy(ABC):
    """Abstract base class for GraphQL order by types.

    All GraphQL order by input types should inherit from this ABC
    to ensure they implement the to_query_order method.
    """

    @abstractmethod
    def to_query_order(self) -> QueryOrder:
        """Convert to repository QueryOrder.

        Returns:
            A QueryOrder (SQLAlchemy UnaryExpression) for ordering query results.
        """
        raise NotImplementedError


@dataclass
class StrawberryGQLContext:
    processors: Processors
    config_provider: ManagerConfigProvider
    event_hub: EventHub
    event_fetcher: EventFetcher
    gql_adapter: BaseGQLAdapter
    data_loaders: DataLoaders
    metric_observer: GraphQLMetricObserver
    adapters: Adapters


# Scope input types for BEP-1041 Resource Group scoped APIs


@strawberry.experimental.pydantic.input(
    model=ResourceGroupDomainScopeDTO,
    name="ResourceGroupDomainScope",
    description="Resource group scope for domain-level operations",
)
class ResourceGroupDomainScope:
    """Scope for domain-level APIs within a resource group context."""

    resource_group_name: str = strawberry.field(
        description="Resource group name to scope the operation"
    )

    def to_pydantic(self) -> ResourceGroupDomainScopeDTO:
        return ResourceGroupDomainScopeDTO(resource_group_name=self.resource_group_name)


@strawberry.experimental.pydantic.input(
    model=ResourceGroupProjectScopeDTO,
    name="ResourceGroupProjectScope",
    description="Resource group + domain scope for project-level operations",
)
class ResourceGroupProjectScope:
    """Scope for project-level APIs within a resource group and domain context."""

    resource_group_name: str = strawberry.field(
        description="Resource group name to scope the operation"
    )
    domain_name: str = strawberry.field(description="Domain name to scope the operation")

    def to_pydantic(self) -> ResourceGroupProjectScopeDTO:
        return ResourceGroupProjectScopeDTO(
            resource_group_name=self.resource_group_name,
            domain_name=self.domain_name,
        )


@strawberry.experimental.pydantic.input(
    model=ResourceGroupUserScopeDTO,
    name="ResourceGroupUserScope",
    description="Resource group + domain + project scope for user-level operations",
)
class ResourceGroupUserScope:
    """Scope for user-level APIs within a resource group, domain, and project context."""

    resource_group_name: str = strawberry.field(
        description="Resource group name to scope the operation"
    )
    domain_name: str = strawberry.field(description="Domain name to scope the operation")
    project_id: str = strawberry.field(description="Project ID to scope the operation")

    def to_pydantic(self) -> ResourceGroupUserScopeDTO:
        return ResourceGroupUserScopeDTO(
            resource_group_name=self.resource_group_name,
            domain_name=self.domain_name,
            project_id=self.project_id,
        )


# Scope input types for Usage Bucket scoped APIs


@strawberry.experimental.pydantic.input(
    model=DomainUsageBucketScopeDTO,
    name="DomainUsageBucketScope",
    description="Domain scope for usage bucket queries",
)
class DomainUsageBucketScope:
    """Scope for domain-level usage bucket APIs."""

    resource_group_name: str = strawberry.field(description="Resource group name")
    domain_name: str = strawberry.field(description="Domain name to retrieve usage buckets for")

    def to_pydantic(self) -> DomainUsageBucketScopeDTO:
        return DomainUsageBucketScopeDTO(
            resource_group_name=self.resource_group_name,
            domain_name=self.domain_name,
        )


@strawberry.experimental.pydantic.input(
    model=ProjectUsageBucketScopeDTO,
    name="ProjectUsageBucketScope",
    description="Project scope for usage bucket queries",
)
class ProjectUsageBucketScope:
    """Scope for project-level usage bucket APIs."""

    resource_group_name: str = strawberry.field(description="Resource group name")
    domain_name: str = strawberry.field(description="Domain name")
    project_id: str = strawberry.field(description="Project ID (will be converted to UUID)")

    def to_pydantic(self) -> ProjectUsageBucketScopeDTO:
        return ProjectUsageBucketScopeDTO(
            resource_group_name=self.resource_group_name,
            domain_name=self.domain_name,
            project_id=self.project_id,
        )


@strawberry.experimental.pydantic.input(
    model=UserUsageBucketScopeDTO,
    name="UserUsageBucketScope",
    description="User scope for usage bucket queries",
)
class UserUsageBucketScope:
    """Scope for user-level usage bucket APIs."""

    resource_group_name: str = strawberry.field(description="Resource group name")
    domain_name: str = strawberry.field(description="Domain name")
    project_id: str = strawberry.field(description="Project ID (will be converted to UUID)")
    user_uuid: str = strawberry.field(description="User UUID (will be converted to UUID)")

    def to_pydantic(self) -> UserUsageBucketScopeDTO:
        return UserUsageBucketScopeDTO(
            resource_group_name=self.resource_group_name,
            domain_name=self.domain_name,
            project_id=self.project_id,
            user_uuid=self.user_uuid,
        )
