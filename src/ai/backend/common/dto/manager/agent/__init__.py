"""
Agent DTOs for Manager API.
"""

from .request import (
    AgentFilter,
    AgentOrder,
    SearchAgentsRequest,
)
from .response import (
    AgentDTO,
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
    "SearchAgentsRequest",
    # Response DTOs
    "AgentDTO",
    "PaginationInfo",
    "SearchAgentsResponse",
    # Types
    "AgentOrderField",
    "AgentStatusEnum",
    "AgentStatusEnumFilter",
    "OrderDirection",
)
