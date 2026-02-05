"""DomainV2 GraphQL API package.

Added in 26.2.0. Provides structured domain management API with typed fields
replacing JSON scalars and organized into logical field groups.
"""

from .resolver import admin_domains_v2, domain_v2
from .types import (
    DomainBasicInfoGQL,
    DomainLifecycleInfoGQL,
    DomainRegistryInfoGQL,
    DomainV2Connection,
    DomainV2Edge,
    DomainV2Filter,
    DomainV2GQL,
    DomainV2OrderBy,
    DomainV2OrderField,
)

__all__ = [
    # Queries
    "domain_v2",
    "admin_domains_v2",
    # Filter and OrderBy
    "DomainV2Filter",
    "DomainV2OrderBy",
    "DomainV2OrderField",
    # Nested types
    "DomainBasicInfoGQL",
    "DomainLifecycleInfoGQL",
    "DomainRegistryInfoGQL",
    # Node types
    "DomainV2GQL",
    "DomainV2Edge",
    "DomainV2Connection",
]
