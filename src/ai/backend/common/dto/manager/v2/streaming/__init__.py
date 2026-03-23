"""
Streaming DTOs v2 for Manager API.
"""

from ai.backend.common.dto.manager.v2.streaming.request import (
    ExecuteInput,
    PtyClientInput,
    PtyPingInput,
    PtyResizeInput,
    PtyRestartInput,
    PtyStdinInput,
    StreamProxyInput,
)
from ai.backend.common.dto.manager.v2.streaming.response import (
    ExecuteResultNode,
    GetStreamAppsPayload,
    PtyOutputNode,
)
from ai.backend.common.dto.manager.v2.streaming.types import (
    ExecuteMode,
    ExecuteResultStatus,
    PtyInputMessageType,
    PtyOutputMessageType,
    ServiceProtocol,
    StreamAppInfoNode,
)

__all__ = (
    # Types (enums + sub-models)
    "ExecuteMode",
    "ExecuteResultStatus",
    "PtyInputMessageType",
    "PtyOutputMessageType",
    "ServiceProtocol",
    "StreamAppInfoNode",
    # Input models (request)
    "ExecuteInput",
    "PtyClientInput",
    "PtyPingInput",
    "PtyResizeInput",
    "PtyRestartInput",
    "PtyStdinInput",
    "StreamProxyInput",
    # Node/Payload models (response)
    "ExecuteResultNode",
    "GetStreamAppsPayload",
    "PtyOutputNode",
)
