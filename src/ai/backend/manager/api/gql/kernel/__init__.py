"""GraphQL types and resolvers for kernel management."""

from __future__ import annotations

from .fetcher import fetch_kernels
from .types import (
    KernelClusterInfoGQL,
    KernelConnectionV2GQL,
    KernelEdgeGQL,
    KernelFilterGQL,
    KernelLifecycleInfoGQL,
    KernelNetworkInfoGQL,
    KernelOrderByGQL,
    KernelOrderFieldGQL,
    KernelResourceInfoGQL,
    KernelSessionInfoGQL,
    KernelStatusFilterGQL,
    KernelStatusGQL,
    KernelUserInfoGQL,
    KernelV2GQL,
    ResourceAllocationGQL,
)

__all__ = [
    # Types
    "KernelClusterInfoGQL",
    "KernelConnectionV2GQL",
    "KernelEdgeGQL",
    "KernelFilterGQL",
    "KernelLifecycleInfoGQL",
    "KernelNetworkInfoGQL",
    "KernelOrderByGQL",
    "KernelOrderFieldGQL",
    "KernelResourceInfoGQL",
    "KernelSessionInfoGQL",
    "KernelStatusFilterGQL",
    "KernelStatusGQL",
    "KernelUserInfoGQL",
    "KernelV2GQL",
    "ResourceAllocationGQL",
    # Fetchers
    "fetch_kernels",
]
