from __future__ import annotations

from .base import SchedulingHistoryAction
from .global_search_replica_group_history import (
    GlobalSearchReplicaGroupHistoryAction,
    GlobalSearchReplicaGroupHistoryActionResult,
)
from .scoped_search_replica_group_history import (
    ScopedSearchReplicaGroupHistoryAction,
    ScopedSearchReplicaGroupHistoryActionResult,
)
from .search_deployment_history import (
    SearchDeploymentHistoryAction,
)
from .search_deployment_scoped_history import (
    SearchDeploymentScopedHistoryAction,
    SearchDeploymentScopedHistoryActionResult,
)
from .search_kernel_history import (
    SearchKernelHistoryAction,
)
from .search_kernel_scoped_history import (
    SearchKernelScopedHistoryAction,
    SearchKernelScopedHistoryActionResult,
)
from .search_route_history import (
    SearchRouteHistoryAction,
)
from .search_route_scoped_history import (
    SearchRouteScopedHistoryAction,
    SearchRouteScopedHistoryActionResult,
)
from .search_session_history import (
    SearchSessionHistoryAction,
)
from .search_session_scoped_history import (
    SearchSessionScopedHistoryAction,
    SearchSessionScopedHistoryActionResult,
)

__all__ = (
    "SchedulingHistoryAction",
    # Admin actions
    "SearchSessionHistoryAction",
    "SearchKernelHistoryAction",
    "SearchDeploymentHistoryAction",
    "GlobalSearchReplicaGroupHistoryAction",
    "GlobalSearchReplicaGroupHistoryActionResult",
    "SearchRouteHistoryAction",
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
