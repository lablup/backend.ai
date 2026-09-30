"""Kernel status sets the manager counts resources and liveness by.

The v1 paths (`registry.py`, `api/gql_legacy`, the REST v1 stream cleanup read)
import these names as they are; the v2 paths are moving to class methods on
`KernelStatus`.
"""

from __future__ import annotations

from ai.backend.manager.data.kernel.types import KernelStatus

__all__ = (
    "AGENT_RESOURCE_OCCUPYING_KERNEL_STATUSES",
    "DEAD_KERNEL_STATUSES",
    "LIVE_STATUS",
    "RESOURCE_USAGE_KERNEL_STATUSES",
    "USER_RESOURCE_OCCUPYING_KERNEL_STATUSES",
)

# statuses to consider when calculating current resource usage
AGENT_RESOURCE_OCCUPYING_KERNEL_STATUSES = tuple(
    e
    for e in KernelStatus
    if e
    not in (
        KernelStatus.TERMINATED,
        KernelStatus.PENDING,
        KernelStatus.CANCELLED,
    )
)

# The same set under the name the per-user concurrency queries use.
USER_RESOURCE_OCCUPYING_KERNEL_STATUSES = AGENT_RESOURCE_OCCUPYING_KERNEL_STATUSES

# statuses to consider when calculating historical resource usage
RESOURCE_USAGE_KERNEL_STATUSES = (
    KernelStatus.TERMINATED,
    KernelStatus.RUNNING,
)

DEAD_KERNEL_STATUSES = (
    KernelStatus.CANCELLED,
    KernelStatus.TERMINATED,
)

LIVE_STATUS = (KernelStatus.RUNNING,)
