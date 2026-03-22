"""
Agent DTOs v2 for Manager API.
"""

from ai.backend.common.dto.manager.v2.agent.request import (
    AgentFilter,
    AgentOrder,
    AgentPathParam,
    SearchAgentsInput,
)
from ai.backend.common.dto.manager.v2.agent.response import (
    AgentNetworkInfo,
    AgentNode,
    AgentResourceInfo,
    AgentResourceStatsPayload,
    AgentStatusInfo,
    AgentSystemInfo,
    GetAgentDetailPayload,
    SearchAgentsPayload,
)
from ai.backend.common.dto.manager.v2.agent.types import (
    AgentOrderField,
    AgentStatusEnum,
    AgentStatusFilter,
    OrderDirection,
)

__all__ = (
    # Types
    "AgentOrderField",
    "AgentStatusEnum",
    "AgentStatusFilter",
    "OrderDirection",
    # Input models (request)
    "AgentFilter",
    "AgentOrder",
    "AgentPathParam",
    "SearchAgentsInput",
    # Node and Payload models (response)
    "AgentNetworkInfo",
    "AgentNode",
    "AgentResourceInfo",
    "AgentResourceStatsPayload",
    "AgentStatusInfo",
    "AgentSystemInfo",
    "GetAgentDetailPayload",
    "SearchAgentsPayload",
)
