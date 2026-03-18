"""
Agent DTOs for Manager API.
"""

from .request import (
    AgentFilter,
    AgentOrder,
    AgentPathParam,
    SearchAgentsRequest,
)
from .response import (
    AgentDTO,
    AgentResourceStatsResponse,
    GetAgentDetailResponse,
    PaginationInfo,
    SearchAgentsResponse,
)
from .types import (
    AgentOrderField,
    AgentStatusEnum,
    AgentStatusEnumFilter,
    OrderDirection,
)

__all__ = (
    # Request DTOs
    "AgentFilter",
    "AgentOrder",
    "AgentPathParam",
    "SearchAgentsRequest",
    # Response DTOs
    "AgentDTO",
    "AgentResourceStatsResponse",
    "GetAgentDetailResponse",
    "PaginationInfo",
    "SearchAgentsResponse",
    # Types
    "AgentOrderField",
    "AgentStatusEnum",
    "AgentStatusEnumFilter",
    "OrderDirection",
)
