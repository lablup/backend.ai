from __future__ import annotations

from abc import ABC, abstractmethod
from dataclasses import dataclass
from typing import TYPE_CHECKING

import strawberry

from ai.backend.manager.api.gql.data_loader.data_loaders import DataLoaders
from ai.backend.manager.api.gql.data_loader.registry import DataLoaderRegistry
from ai.backend.manager.config.provider import ManagerConfigProvider
from ai.backend.manager.repositories.base import QueryCondition, QueryOrder
from ai.backend.manager.services.processors import Processors

if TYPE_CHECKING:
    from ai.backend.common.events.fetcher import EventFetcher
    from ai.backend.common.events.hub.hub import EventHub
    from ai.backend.manager.api.gql.adapter import BaseGQLAdapter


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
    dataloader_registry: DataLoaderRegistry  # TODO: Remove this.
    gql_adapter: BaseGQLAdapter
    data_loaders: DataLoaders


# Scope input types for BEP-1041 Resource Group scoped APIs


@strawberry.input(description="Resource group scope for domain-level operations")
class ResourceGroupDomainScope:
    """Scope for domain-level APIs within a resource group context."""

    resource_group: str = strawberry.field(description="Resource group name to scope the operation")


@strawberry.input(description="Resource group + domain scope for project-level operations")
class ResourceGroupProjectScope:
    """Scope for project-level APIs within a resource group and domain context."""

    resource_group: str = strawberry.field(description="Resource group name to scope the operation")
    domain_name: str = strawberry.field(description="Domain name to scope the operation")


@strawberry.input(description="Resource group + domain + project scope for user-level operations")
class ResourceGroupUserScope:
    """Scope for user-level APIs within a resource group, domain, and project context."""

    resource_group: str = strawberry.field(description="Resource group name to scope the operation")
    domain_name: str = strawberry.field(description="Domain name to scope the operation")
    project_id: str = strawberry.field(description="Project ID to scope the operation")
