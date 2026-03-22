"""
Scheduling history DTOs v2 for Manager API.
"""

from ai.backend.common.dto.manager.v2.scheduling_history.request import (
    AdminSearchDeploymentHistoriesInput,
    AdminSearchRouteHistoriesInput,
    AdminSearchSessionHistoriesInput,
    DeploymentHistoryFilter,
    DeploymentHistoryOrder,
    RouteHistoryFilter,
    RouteHistoryOrder,
    SearchDeploymentHistoryInput,
    SearchRouteHistoryInput,
    SearchSessionHistoryInput,
    SessionHistoryFilter,
    SessionHistoryOrder,
)
from ai.backend.common.dto.manager.v2.scheduling_history.response import (
    AdminSearchDeploymentHistoriesPayload,
    AdminSearchRouteHistoriesPayload,
    AdminSearchSessionHistoriesPayload,
    DeploymentHistoryNode,
    ListDeploymentHistoryPayload,
    ListRouteHistoryPayload,
    ListSessionHistoryPayload,
    RouteHistoryNode,
    SessionHistoryNode,
)
from ai.backend.common.dto.manager.v2.scheduling_history.types import (
    DeploymentHistoryOrderField,
    DeploymentHistoryScopeDTO,
    OrderDirection,
    RouteHistoryOrderField,
    RouteHistoryScopeDTO,
    SchedulingResultType,
    SessionHistoryOrderField,
    SessionHistoryScopeDTO,
    SubStepResultInfo,
)

__all__ = (
    # Types
    "DeploymentHistoryOrderField",
    "DeploymentHistoryScopeDTO",
    "OrderDirection",
    "RouteHistoryOrderField",
    "RouteHistoryScopeDTO",
    "SchedulingResultType",
    "SessionHistoryOrderField",
    "SessionHistoryScopeDTO",
    "SubStepResultInfo",
    # Input models (request)
    "AdminSearchDeploymentHistoriesInput",
    "AdminSearchRouteHistoriesInput",
    "AdminSearchSessionHistoriesInput",
    "DeploymentHistoryFilter",
    "DeploymentHistoryOrder",
    "RouteHistoryFilter",
    "RouteHistoryOrder",
    "SearchDeploymentHistoryInput",
    "SearchRouteHistoryInput",
    "SearchSessionHistoryInput",
    "SessionHistoryFilter",
    "SessionHistoryOrder",
    # Response models
    "AdminSearchDeploymentHistoriesPayload",
    "AdminSearchRouteHistoriesPayload",
    "AdminSearchSessionHistoriesPayload",
    "DeploymentHistoryNode",
    "ListDeploymentHistoryPayload",
    "ListRouteHistoryPayload",
    "ListSessionHistoryPayload",
    "RouteHistoryNode",
    "SessionHistoryNode",
)
