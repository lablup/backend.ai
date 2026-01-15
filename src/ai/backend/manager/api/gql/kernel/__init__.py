"""GraphQL types and resolvers for kernel management."""

from __future__ import annotations

from .fetcher import fetch_kernels_by_agent
from .types import (
    KernelClusterInfoGQL,
    KernelConnectionV2GQL,
    KernelEdgeGQL,
    KernelFilterGQL,
    KernelGQL,
    KernelImageInfoGQL,
    KernelLifecycleInfoGQL,
    KernelMetadataInfoGQL,
    KernelMetricsInfoGQL,
    KernelNetworkInfoGQL,
    KernelOrderByGQL,
    KernelOrderFieldGQL,
    KernelResourceInfoGQL,
    KernelRuntimeInfoGQL,
    KernelSessionInfoGQL,
    KernelStatusGQL,
    KernelUserPermissionInfoGQL,
)

__all__ = [
    # Types
    "KernelClusterInfoGQL",
    "KernelConnectionV2GQL",
    "KernelEdgeGQL",
    "KernelFilterGQL",
    "KernelGQL",
    "KernelImageInfoGQL",
    "KernelLifecycleInfoGQL",
    "KernelMetadataInfoGQL",
    "KernelMetricsInfoGQL",
    "KernelNetworkInfoGQL",
    "KernelOrderByGQL",
    "KernelOrderFieldGQL",
    "KernelResourceInfoGQL",
    "KernelRuntimeInfoGQL",
    "KernelSessionInfoGQL",
    "KernelStatusGQL",
    "KernelUserPermissionInfoGQL",
    # Fetchers
    "fetch_kernels_by_agent",
]
