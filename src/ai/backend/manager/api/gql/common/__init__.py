"""Common GraphQL types shared across multiple domains."""

from __future__ import annotations

from ai.backend.common.types import (
    ServicePortProtocols,
    SessionResult,
    SessionTypes,
)

from .types import (
    ResourceOptsEntryGQL,
    ResourceOptsEntryInput,
    ResourceOptsGQL,
    ResourceOptsInput,
    ServicePortEntryGQL,
    ServicePortsGQL,
    SessionV2ResultGQL,
    SessionV2TypeGQL,
)

__all__ = [
    # Re-exported enums from ai.backend.common.types
    "ServicePortProtocols",
    "SessionResult",
    "SessionTypes",
    # GQL types
    "ResourceOptsEntryGQL",
    "ResourceOptsEntryInput",
    "ResourceOptsGQL",
    "ResourceOptsInput",
    "ServicePortEntryGQL",
    "ServicePortsGQL",
    "SessionV2ResultGQL",
    "SessionV2TypeGQL",
]
