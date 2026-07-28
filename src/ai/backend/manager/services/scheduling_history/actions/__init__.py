from __future__ import annotations

from .base import SchedulingHistoryAction
from .global_search_replica_group_history import (
    GlobalSearchReplicaGroupHistoryAction,
    GlobalSearchReplicaGroupHistoryActionResult,
)
from .resolve_kernel_session import (
    ResolveKernelSessionAction,
    ResolveKernelSessionActionResult,
)
from .scoped_search_replica_group_history import (
    ScopedSearchReplicaGroupHistoryAction,
    ScopedSearchReplicaGroupHistoryActionResult,
)
from .search_deployment_history import (
    SearchDeploymentHistoryAction,
    SearchDeploymentHistoryActionResult,
)
from .search_deployment_scoped_history import (
    SearchDeploymentScopedHistoryAction,
    SearchDeploymentScopedHistoryActionResult,
)
from .search_kernel_history import (
    SearchKernelHistoryAction,
    SearchKernelHistoryActionResult,
)
from .search_kernel_scoped_history import (
    SearchKernelScopedHistoryAction,
    SearchKernelScopedHistoryActionResult,
)
from .search_route_history import (
    SearchRouteHistoryAction,
    SearchRouteHistoryActionResult,
)
from .search_route_scoped_history import (
    SearchRouteScopedHistoryAction,
    SearchRouteScopedHistoryActionResult,
)
from .search_session_history import (
    SearchSessionHistoryAction,
    SearchSessionHistoryActionResult,
)
from .search_session_scoped_history import (
    SearchSessionScopedHistoryAction,
    SearchSessionScopedHistoryActionResult,
)

__all__ = (
    "ResolveKernelSessionAction",
    "ResolveKernelSessionActionResult",
    "SchedulingHistoryAction",
    # Admin actions
    "SearchSessionHistoryAction",
    "SearchSessionHistoryActionResult",
    "SearchKernelHistoryAction",
    "SearchKernelHistoryActionResult",
    "SearchDeploymentHistoryAction",
    "SearchDeploymentHistoryActionResult",
    "GlobalSearchReplicaGroupHistoryAction",
    "GlobalSearchReplicaGroupHistoryActionResult",
    "SearchRouteHistoryAction",
    "SearchRouteHistoryActionResult",
    # Scoped actions (added in 26.2.0)
    "SearchSessionScopedHistoryAction",
    "SearchSessionScopedHistoryActionResult",
    "SearchKernelScopedHistoryAction",
    "SearchKernelScopedHistoryActionResult",
    "SearchDeploymentScopedHistoryAction",
    "SearchDeploymentScopedHistoryActionResult",
    "ScopedSearchReplicaGroupHistoryAction",
    "ScopedSearchReplicaGroupHistoryActionResult",
    "SearchRouteScopedHistoryAction",
    "SearchRouteScopedHistoryActionResult",
)
