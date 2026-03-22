"""Common DTOs for scaling group API."""

from __future__ import annotations

from .request import (
    ListScalingGroupsRequest,
    WsproxyVersionPathParam,
    WsproxyVersionQueryParam,
)
from .response import (
    ListScalingGroupsResponse,
    WsproxyVersionResponse,
)

# Backward-compatible alias: client SDK uses GetWsproxyVersionResponse
GetWsproxyVersionResponse = WsproxyVersionResponse

__all__ = (
    "ListScalingGroupsRequest",
    "WsproxyVersionPathParam",
    "WsproxyVersionQueryParam",
    "ListScalingGroupsResponse",
    "WsproxyVersionResponse",
    "GetWsproxyVersionResponse",
)
