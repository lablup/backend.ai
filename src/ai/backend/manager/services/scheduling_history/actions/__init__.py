from __future__ import annotations

from .base import SchedulingHistoryAction
from .search_deployment_history import (
    SearchDeploymentHistoryAction,
    SearchDeploymentHistoryActionResult,
)
from .search_deployment_scoped_history import (
    SearchDeploymentScopedHistoryAction,
    SearchDeploymentScopedHistoryActionResult,
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
    "SchedulingHistoryAction",
    # Admin actions
    "SearchSessionHistoryAction",
    "SearchSessionHistoryActionResult",
    "SearchDeploymentHistoryAction",
    "SearchDeploymentHistoryActionResult",
    "SearchRouteHistoryAction",
    "SearchRouteHistoryActionResult",
    # Scoped actions (added in 26.2.0)
    "SearchSessionScopedHistoryAction",
    "SearchSessionScopedHistoryActionResult",
    "SearchDeploymentScopedHistoryAction",
    "SearchDeploymentScopedHistoryActionResult",
    "SearchRouteScopedHistoryAction",
    "SearchRouteScopedHistoryActionResult",
)
