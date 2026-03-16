"""
Operations DTOs v2 for Manager API.
"""

from ai.backend.common.dto.manager.v2.operations.request import (
    AppendErrorLogInput,
    ClearErrorLogInput,
    ListErrorLogsInput,
    PerformSchedulerOpsInput,
    SubscribeBackgroundTaskInput,
    SubscribeSessionEventsInput,
    UpdateAnnouncementInput,
    UpdateManagerStatusInput,
)
from ai.backend.common.dto.manager.v2.operations.response import (
    AnnouncementNode,
    AppendErrorLogPayload,
    ClearErrorLogPayload,
    ErrorLogNode,
    ListErrorLogsPayload,
    ManagerNodeInfo,
    ManagerStatusPayload,
)
from ai.backend.common.dto.manager.v2.operations.types import (
    ErrorLogContextInfo,
    ErrorLogOrderField,
    ErrorLogRequestInfo,
    ErrorLogSeverity,
    ManagerStatus,
    OrderDirection,
    SchedulerOps,
)

__all__ = (
    # Types
    "ErrorLogContextInfo",
    "ErrorLogOrderField",
    "ErrorLogRequestInfo",
    "ErrorLogSeverity",
    "ManagerStatus",
    "OrderDirection",
    "SchedulerOps",
    # Input models (request)
    "AppendErrorLogInput",
    "ClearErrorLogInput",
    "ListErrorLogsInput",
    "PerformSchedulerOpsInput",
    "SubscribeBackgroundTaskInput",
    "SubscribeSessionEventsInput",
    "UpdateAnnouncementInput",
    "UpdateManagerStatusInput",
    # Node and Payload models (response)
    "AnnouncementNode",
    "AppendErrorLogPayload",
    "ClearErrorLogPayload",
    "ErrorLogNode",
    "ListErrorLogsPayload",
    "ManagerNodeInfo",
    "ManagerStatusPayload",
)
