from datetime import datetime
from typing import Optional

import strawberry
from strawberry.relay import Node, NodeID
from strawberry.scalars import JSON

from ai.backend.manager.data.agent.types import AgentStatus
from ai.backend.manager.models.rbac.permission_defs import AgentPermission


@strawberry.type(description="Resource-related information for an agent")
class AgentResourceInfo:
    available_slots: JSON
    occupied_slots: JSON
    compute_plugins: JSON


@strawberry.type(description="Status and lifecycle information for an agent")
class AgentStatusInfo:
    status: AgentStatus
    status_changed: datetime
    first_contact: datetime
    lost_at: Optional[datetime]
    schedulable: bool


@strawberry.type(description="System and configuration information for an agent")
class AgentSystemInfo:
    architecture: str
    version: str
    auto_terminate_abusing_kernel: bool = strawberry.field(
        description="Not used anymore, present for schema consistency."
    )


@strawberry.type(description="Network-related information for an agent")
class AgentNetworkInfo:
    region: str
    addr: str = strawberry.field(
        description="Agent's address with port. (bind/advertised host:port)"
    )


@strawberry.type(description="Strawberry-based Agent type replacing AgentNode. Added in 25.18.0.")
class AgentV2(Node):
    id: NodeID[str]
    resource_info: AgentResourceInfo
    status_info: AgentStatusInfo
    system_info: AgentSystemInfo
    network_info: AgentNetworkInfo
    permissions: list[AgentPermission]
    scaling_group: str
