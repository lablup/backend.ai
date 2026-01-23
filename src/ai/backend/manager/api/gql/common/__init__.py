"""Common GraphQL types shared across multiple domains."""

from __future__ import annotations

from ai.backend.common.types import (
    MountPermission,
    ServicePortProtocols,
    SessionResult,
    SessionTypes,
    VFolderUsageMode,
)

from .types import (
    DotfileInfoGQL,
    MetricStatGQL,
    MetricValueGQL,
    ResourceOptsEntryGQL,
    ResourceOptsEntryInput,
    ResourceOptsGQL,
    ResourceOptsInput,
    SchedulerInfoGQL,
    SchedulerPredicateGQL,
    ServicePortEntryGQL,
    ServicePortsGQL,
    SSHKeypairGQL,
    VFolderMountGQL,
)

__all__ = [
    # Re-exported enums from ai.backend.common.types
    "MountPermission",
    "ServicePortProtocols",
    "SessionResult",
    "SessionTypes",
    "VFolderUsageMode",
    # GQL types
    "DotfileInfoGQL",
    "MetricStatGQL",
    "MetricValueGQL",
    "ResourceOptsEntryGQL",
    "ResourceOptsEntryInput",
    "ResourceOptsGQL",
    "ResourceOptsInput",
    "SchedulerInfoGQL",
    "SchedulerPredicateGQL",
    "ServicePortEntryGQL",
    "ServicePortsGQL",
    "SSHKeypairGQL",
    "VFolderMountGQL",
]
