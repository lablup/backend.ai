"""DomainV2 GraphQL types package."""

from .nested import (
    DomainBasicInfoGQL,
    DomainLifecycleInfoGQL,
    DomainRegistryInfoGQL,
)
from .node import DomainV2Connection, DomainV2Edge, DomainV2GQL

__all__ = [
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
