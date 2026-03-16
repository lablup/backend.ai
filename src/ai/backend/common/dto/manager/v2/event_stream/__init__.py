"""
Event stream DTOs v2 for Manager API.
"""

from ai.backend.common.dto.manager.v2.event_stream.request import (
    BackgroundTaskEventSubscribeInput,
    SessionEventSubscribeInput,
)
from ai.backend.common.dto.manager.v2.event_stream.response import (
    BgtaskCancelledNode,
    BgtaskDoneNode,
    BgtaskFailedNode,
    BgtaskPartialSuccessNode,
    BgtaskUpdatedNode,
    SessionEventNode,
    SessionKernelEventNode,
)
from ai.backend.common.dto.manager.v2.event_stream.types import (
    BgtaskSSEEventName,
    SessionEventScope,
)

__all__ = (
    # Types
    "BgtaskSSEEventName",
    "SessionEventScope",
    # Input models (request)
    "BackgroundTaskEventSubscribeInput",
    "SessionEventSubscribeInput",
    # Node models (response)
    "BgtaskCancelledNode",
    "BgtaskDoneNode",
    "BgtaskFailedNode",
    "BgtaskPartialSuccessNode",
    "BgtaskUpdatedNode",
    "SessionEventNode",
    "SessionKernelEventNode",
)
