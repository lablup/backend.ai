"""
Streaming DTOs for Manager API.
"""

from .response import GetStreamAppsResponse
from .types import (
    BackgroundTaskEventParams,
    BgtaskCancelledPayload,
    BgtaskDonePayload,
    BgtaskFailedPayload,
    BgtaskPartialSuccessPayload,
    BgtaskSSEEventName,
    BgtaskUpdatedPayload,
    ExecuteMode,
    ExecuteRequest,
    ExecuteResult,
    ExecuteResultStatus,
    PtyClientMessage,
    PtyInputMessageType,
    PtyOutputMessage,
    PtyOutputMessageType,
    PtyPingMessage,
    PtyResizeMessage,
    PtyRestartMessage,
    PtyStdinMessage,
    ServiceProtocol,
    SessionEventParams,
    SessionEventScope,
    StreamAppInfo,
    StreamProxyParams,
)

__all__ = (
    # Enums
    "BgtaskSSEEventName",
    "ExecuteMode",
    "ExecuteResultStatus",
    "PtyInputMessageType",
    "PtyOutputMessageType",
    "ServiceProtocol",
    "SessionEventScope",
    # PTY WebSocket messages
    "PtyClientMessage",
    "PtyOutputMessage",
    "PtyPingMessage",
    "PtyResizeMessage",
    "PtyRestartMessage",
    "PtyStdinMessage",
    # Execute WebSocket messages
    "ExecuteRequest",
    "ExecuteResult",
    # Proxy / App
    "GetStreamAppsResponse",
    "StreamAppInfo",
    "StreamProxyParams",
    # SSE event params
    "BackgroundTaskEventParams",
    "SessionEventParams",
    # SSE event payloads
    "BgtaskCancelledPayload",
    "BgtaskDonePayload",
    "BgtaskFailedPayload",
    "BgtaskPartialSuccessPayload",
    "BgtaskUpdatedPayload",
)
