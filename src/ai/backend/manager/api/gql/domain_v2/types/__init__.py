"""DomainV2 GraphQL types package."""

from .filters import (
    DomainProjectNestedFilter,
    DomainUserNestedFilter,
    DomainV2Filter,
    DomainV2OrderBy,
    DomainV2OrderField,
)
from .nested import (
    DomainBasicInfoGQL,
    DomainLifecycleInfoGQL,
    DomainRegistryInfoGQL,
)
from .node import DomainV2Connection, DomainV2Edge, DomainV2GQL

__all__ = [
    # Filter and OrderBy
    "DomainProjectNestedFilter",
    "DomainUserNestedFilter",
    "DomainV2Filter",
    "DomainV2OrderBy",
    "DomainV2OrderField",
    # Nested types - Basic
    "DomainBasicInfoGQL",
    # Nested types - Registry
    "DomainRegistryInfoGQL",
    # Nested types - Lifecycle
    "DomainLifecycleInfoGQL",
    # Node types
    "DomainV2GQL",
    "DomainV2Edge",
    "DomainV2Connection",
]
