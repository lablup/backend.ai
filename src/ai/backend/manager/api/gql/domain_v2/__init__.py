"""DomainV2 GraphQL API package.

This package provides GraphQL types, resolvers, and data loaders for the DomainV2 API.
DomainV2 replaces the legacy DomainNode with structured field groups instead of JSON scalars.

Package structure:
- types/: GraphQL type definitions (nested types, node, edge, connection)
- resolver/: Query and mutation resolvers (to be implemented)
- fetcher/: Data loaders for efficient batch fetching (to be implemented)
"""

from .types import (
    DomainBasicInfoGQL,
    DomainLifecycleInfoGQL,
    DomainRegistryInfoGQL,
    DomainV2Connection,
    DomainV2Edge,
    DomainV2GQL,
)

__all__ = [
    "DomainBasicInfoGQL",
    "DomainLifecycleInfoGQL",
    "DomainRegistryInfoGQL",
    "DomainV2GQL",
    "DomainV2Edge",
    "DomainV2Connection",
]
