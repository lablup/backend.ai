"""
Scheduling history DTOs v2 for Manager API.
"""

from ai.backend.common.dto.manager.v2.scheduling_history.request import (
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
    DeploymentHistoryNode,
    ListDeploymentHistoryPayload,
    ListRouteHistoryPayload,
    ListSessionHistoryPayload,
    RouteHistoryNode,
    SessionHistoryNode,
)
from ai.backend.common.dto.manager.v2.scheduling_history.types import (
    DeploymentHistoryOrderField,
    OrderDirection,
    RouteHistoryOrderField,
    SchedulingResultType,
    SessionHistoryOrderField,
    SubStepResultInfo,
)

__all__ = (
    # Types
    "DeploymentHistoryOrderField",
    "OrderDirection",
    "RouteHistoryOrderField",
    "SchedulingResultType",
    "SessionHistoryOrderField",
    "SubStepResultInfo",
    # Input models (request)
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
    "DeploymentHistoryNode",
    "ListDeploymentHistoryPayload",
    "ListRouteHistoryPayload",
    "ListSessionHistoryPayload",
    "RouteHistoryNode",
    "SessionHistoryNode",
)
