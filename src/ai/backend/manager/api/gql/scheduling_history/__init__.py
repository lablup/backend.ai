from __future__ import annotations

from .resolver import (
    DeploymentHistoryConnection,
    RouteHistoryConnection,
    SessionSchedulingHistoryConnection,
    admin_deployment_histories,
    admin_route_histories,
    admin_session_scheduling_histories,
    deployment_histories,
    deployment_scoped_scheduling_histories,
    route_histories,
    route_scoped_scheduling_histories,
    session_scheduling_histories,
    session_scoped_scheduling_histories,
)
from .types import (
    DeploymentHistory,
    DeploymentHistoryFilter,
    DeploymentHistoryOrderBy,
    DeploymentScope,
    RouteHistory,
    RouteHistoryFilter,
    RouteHistoryOrderBy,
    RouteScope,
    SchedulingResultGQL,
    SessionSchedulingHistory,
    SessionSchedulingHistoryFilter,
    SessionSchedulingHistoryOrderBy,
    SessionScope,
    SubStepResultGQL,
)

__all__ = (
    # Enums
    "SchedulingResultGQL",
    # Types
    "SubStepResultGQL",
    "SessionSchedulingHistory",
    "DeploymentHistory",
    "RouteHistory",
    # Filters
    "SessionSchedulingHistoryFilter",
    "SessionSchedulingHistoryOrderBy",
    "DeploymentHistoryFilter",
    "DeploymentHistoryOrderBy",
    "RouteHistoryFilter",
    "RouteHistoryOrderBy",
    # Scope types (added in 26.2.0)
    "SessionScope",
    "DeploymentScope",
    "RouteScope",
    # Connections
    "SessionSchedulingHistoryConnection",
    "DeploymentHistoryConnection",
    "RouteHistoryConnection",
    # Queries - Admin
    "admin_session_scheduling_histories",
    "admin_deployment_histories",
    "admin_route_histories",
    # Queries - Scoped (added in 26.2.0)
    "session_scoped_scheduling_histories",
    "deployment_scoped_scheduling_histories",
    "route_scoped_scheduling_histories",
    # Queries - Legacy (deprecated)
    "session_scheduling_histories",
    "deployment_histories",
    "route_histories",
)
