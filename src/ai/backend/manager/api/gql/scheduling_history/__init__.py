from __future__ import annotations

from .resolver import (
    DeploymentHistoryConnection,
    KernelSchedulingHistoryConnectionGQL,
    RouteHistoryConnection,
    SessionSchedulingHistoryConnection,
    admin_deployment_histories,
    admin_kernel_scheduling_histories,
    admin_route_histories,
    admin_session_scheduling_histories,
    deployment_histories,
    deployment_scoped_scheduling_histories,
    route_histories,
    route_scoped_scheduling_histories,
    scoped_kernel_scheduling_histories,
    session_scheduling_histories,
    session_scoped_scheduling_histories,
)
from .types import (
    DeploymentHistory,
    DeploymentHistoryFilter,
    DeploymentHistoryOrderBy,
    DeploymentScope,
    KernelSchedulingHistoryFilterGQL,
    KernelSchedulingHistoryGQL,
    KernelSchedulingHistoryOrderByGQL,
    KernelScopeGQL,
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
    "KernelSchedulingHistoryGQL",
    "DeploymentHistory",
    "RouteHistory",
    # Filters
    "SessionSchedulingHistoryFilter",
    "SessionSchedulingHistoryOrderBy",
    "KernelSchedulingHistoryFilterGQL",
    "KernelSchedulingHistoryOrderByGQL",
    "DeploymentHistoryFilter",
    "DeploymentHistoryOrderBy",
    "RouteHistoryFilter",
    "RouteHistoryOrderBy",
    # Scope types (added in 26.2.0)
    "SessionScope",
    "KernelScopeGQL",
    "DeploymentScope",
    "RouteScope",
    # Connections
    "SessionSchedulingHistoryConnection",
    "KernelSchedulingHistoryConnectionGQL",
    "DeploymentHistoryConnection",
    "RouteHistoryConnection",
    # Queries - Admin
    "admin_session_scheduling_histories",
    "admin_kernel_scheduling_histories",
    "admin_deployment_histories",
    "admin_route_histories",
    # Queries - Scoped (added in 26.2.0)
    "session_scoped_scheduling_histories",
    "scoped_kernel_scheduling_histories",
    "deployment_scoped_scheduling_histories",
    "route_scoped_scheduling_histories",
    # Queries - Legacy (deprecated)
    "session_scheduling_histories",
    "deployment_histories",
    "route_histories",
)
