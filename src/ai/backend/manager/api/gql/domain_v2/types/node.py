"""DomainV2 GraphQL Node, Edge, and Connection types."""

from __future__ import annotations

from typing import TYPE_CHECKING, Any, Self

import strawberry
from strawberry import ID
from strawberry.relay import Connection, Edge, Node, NodeID

from .nested import (
    DomainBasicInfoGQL,
    DomainLifecycleInfoGQL,
    DomainRegistryInfoGQL,
)

if TYPE_CHECKING:
    from ai.backend.manager.data.domain.types import DomainData


@strawberry.federation.type(
    keys=["id"],
    name="DomainV2",
    description=(
        "Added in 26.2.0. Domain entity with structured field groups. "
        "Formerly DomainNode. Provides comprehensive domain information organized "
        "into logical categories: basic_info (identity), registry (container registries), "
        "and lifecycle (status/timestamps). "
        "All fields use typed structures instead of JSON scalars. "
        "Resource allocation and storage permissions are provided through separate dedicated APIs."
    ),
)
class DomainV2GQL(Node):
    """Domain entity with structured field groups."""

    id: NodeID[str] = strawberry.field(description="Domain name (primary key).")
    basic_info: DomainBasicInfoGQL = strawberry.field(
        description="Basic domain information including name and description."
    )
    registry: DomainRegistryInfoGQL = strawberry.field(
        description="Container registry configuration."
    )
    lifecycle: DomainLifecycleInfoGQL = strawberry.field(
        description="Lifecycle information including activation status and timestamps."
    )

    @classmethod
    def from_data(
        cls,
        data: DomainData,
    ) -> Self:
        """Convert DomainData to GraphQL type.

        Args:
            data: DomainData instance from the data layer.

        Returns:
            DomainV2GQL instance with structured field groups.

        Note:
            - All fields are directly from DomainRow (no external lookups)
            - No JSON scalars are used in the output
            - Primary key is domain name (string), not UUID
            - ResourceSlot and storage permissions are excluded; use dedicated APIs
            - Dotfiles (binary data) is excluded; use query_domain_dotfiles()
        """
        return cls(
            id=ID(data.name),  # name is the primary key
            basic_info=DomainBasicInfoGQL(
                name=data.name,
                description=data.description,
                integration_id=data.integration_id,
            ),
            registry=DomainRegistryInfoGQL(
                allowed_docker_registries=data.allowed_docker_registries,
            ),
            lifecycle=DomainLifecycleInfoGQL(
                is_active=data.is_active,
                created_at=data.created_at,
                modified_at=data.modified_at,
            ),
        )


DomainV2Edge = Edge[DomainV2GQL]


@strawberry.type(
    description=(
        "Added in 26.2.0. Paginated connection for domain records. "
        "Provides relay-style cursor-based pagination for efficient traversal of domain data. "
        "Use 'edges' to access individual records with cursor information, "
        "or 'nodes' for direct data access."
    )
)
class DomainV2Connection(Connection[DomainV2GQL]):
    """Paginated connection for domain records."""

    count: int = strawberry.field(
        description="Total number of domain records matching the query criteria."
    )

    def __init__(self, *args: Any, count: int, **kwargs: Any) -> None:
        super().__init__(*args, **kwargs)
        self.count = count
