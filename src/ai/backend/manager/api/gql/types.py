from __future__ import annotations

from abc import ABC
from dataclasses import dataclass
from typing import TYPE_CHECKING

from ai.backend.common.dto.manager.v2.fair_share.types import (
    DomainUsageBucketScopeDTO,
    ProjectUsageBucketScopeDTO,
    ResourceGroupDomainScopeDTO,
    ResourceGroupProjectScopeDTO,
    ResourceGroupUserScopeDTO,
    UserUsageBucketScopeDTO,
)
from ai.backend.manager.api.gql.data_loader.data_loaders import DataLoaders
from ai.backend.manager.api.gql.decorators import (
    BackendAIGQLMeta,
    PydanticInputMixin,
    gql_field,
    gql_pydantic_input,
)
from ai.backend.manager.config.provider import ManagerConfigProvider

if TYPE_CHECKING:
    from ai.backend.common.events.fetcher import EventFetcher
    from ai.backend.common.events.hub.hub import EventHub
    from ai.backend.common.metrics.metric import GraphQLMetricObserver
    from ai.backend.manager.api.adapters.registry import Adapters
    from ai.backend.manager.api.gql.adapter import BaseGQLAdapter


class GQLFilter(ABC):
    """Base class for GraphQL filter types."""


class GQLOrderBy(ABC):
    """Base class for GraphQL order by types."""


@dataclass
class StrawberryGQLContext:
    config_provider: ManagerConfigProvider
    event_hub: EventHub
    event_fetcher: EventFetcher
    gql_adapter: BaseGQLAdapter
    data_loaders: DataLoaders
    metric_observer: GraphQLMetricObserver
    adapters: Adapters


# Scope input types for BEP-1041 Resource Group scoped APIs


@gql_pydantic_input(
    BackendAIGQLMeta(
        description="Resource group scope for domain-level operations", added_version="24.09.0"
    ),
    name="ResourceGroupDomainScope",
)
class ResourceGroupDomainScope(PydanticInputMixin[ResourceGroupDomainScopeDTO]):
    """Scope for domain-level APIs within a resource group context."""

    resource_group_name: str = gql_field(description="Resource group name to scope the operation")


@gql_pydantic_input(
    BackendAIGQLMeta(
        description="Resource group + domain scope for project-level operations",
        added_version="24.09.0",
    ),
    name="ResourceGroupProjectScope",
)
class ResourceGroupProjectScope(PydanticInputMixin[ResourceGroupProjectScopeDTO]):
    """Scope for project-level APIs within a resource group and domain context."""

    resource_group_name: str = gql_field(description="Resource group name to scope the operation")
    domain_name: str = gql_field(description="Domain name to scope the operation")


@gql_pydantic_input(
    BackendAIGQLMeta(
        description="Resource group + domain + project scope for user-level operations",
        added_version="24.09.0",
    ),
    name="ResourceGroupUserScope",
)
class ResourceGroupUserScope(PydanticInputMixin[ResourceGroupUserScopeDTO]):
    """Scope for user-level APIs within a resource group, domain, and project context."""

    resource_group_name: str = gql_field(description="Resource group name to scope the operation")
    domain_name: str = gql_field(description="Domain name to scope the operation")
    project_id: str = gql_field(description="Project ID to scope the operation")


# Scope input types for Usage Bucket scoped APIs


@gql_pydantic_input(
    BackendAIGQLMeta(description="Domain scope for usage bucket queries", added_version="24.09.0"),
    name="DomainUsageBucketScope",
)
class DomainUsageBucketScope(PydanticInputMixin[DomainUsageBucketScopeDTO]):
    """Scope for domain-level usage bucket APIs."""

    resource_group_name: str = gql_field(description="Resource group name")
    domain_name: str = gql_field(description="Domain name to retrieve usage buckets for")


@gql_pydantic_input(
    BackendAIGQLMeta(description="Project scope for usage bucket queries", added_version="24.09.0"),
    name="ProjectUsageBucketScope",
)
class ProjectUsageBucketScope(PydanticInputMixin[ProjectUsageBucketScopeDTO]):
    """Scope for project-level usage bucket APIs."""

    resource_group_name: str = gql_field(description="Resource group name")
    domain_name: str = gql_field(description="Domain name")
    project_id: str = gql_field(description="Project ID (will be converted to UUID)")


@gql_pydantic_input(
    BackendAIGQLMeta(description="User scope for usage bucket queries", added_version="24.09.0"),
    name="UserUsageBucketScope",
)
class UserUsageBucketScope(PydanticInputMixin[UserUsageBucketScopeDTO]):
    """Scope for user-level usage bucket APIs."""

    resource_group_name: str = gql_field(description="Resource group name")
    domain_name: str = gql_field(description="Domain name")
    project_id: str = gql_field(description="Project ID (will be converted to UUID)")
    user_uuid: str = gql_field(description="User UUID (will be converted to UUID)")
