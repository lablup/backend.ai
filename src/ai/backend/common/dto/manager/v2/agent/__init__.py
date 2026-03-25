"""
Agent DTOs v2 for Manager API.
"""

from ai.backend.common.dto.manager.v2.agent.request import (
    AdminSearchAgentsInput,
    AgentFilter,
    AgentOrder,
    AgentPathParam,
    SearchAgentsInput,
)
from ai.backend.common.dto.manager.v2.agent.response import (
    AdminSearchAgentsPayload,
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
    "AdminSearchAgentsInput",
    "AgentFilter",
    "AgentOrder",
    "AgentPathParam",
    "SearchAgentsInput",
    # Node and Payload models (response)
    "AdminSearchAgentsPayload",
    "AgentNetworkInfo",
    "AgentNode",
    "AgentResourceInfo",
    "AgentResourceStatsPayload",
    "AgentStatusInfo",
    "AgentSystemInfo",
    "GetAgentDetailPayload",
    "SearchAgentsPayload",
)
