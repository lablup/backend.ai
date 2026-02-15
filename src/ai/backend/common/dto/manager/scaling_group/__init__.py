"""
Scaling Group DTOs for Manager API.
"""

from .request import (
    ListScalingGroupsQueryParams,
)
from .response import (
    GetWsproxyVersionResponse,
    ListScalingGroupsResponse,
    ScalingGroupDTO,
)

__all__ = (
    # Request
    "ListScalingGroupsQueryParams",
    # Response
    "ScalingGroupDTO",
    "ListScalingGroupsResponse",
    "GetWsproxyVersionResponse",
)
