from datetime import datetime
from enum import StrEnum
from typing import Optional

import strawberry
from strawberry.relay import Node, NodeID
from strawberry.scalars import JSON

from ai.backend.manager.api.gql.base import OrderDirection, StringFilter
from ai.backend.manager.data.agent.types import AgentStatus
from ai.backend.manager.models.rbac.permission_defs import AgentPermission
from ai.backend.manager.repositories.agent.options import AgentConditions, AgentOrders
from ai.backend.manager.repositories.base import (
    QueryCondition,
    QueryOrder,
    combine_conditions_or,
    negate_conditions,
)


@strawberry.enum(description="Added in 25.18.0. Fields by which agents can be ordered")
class AgentOrderField(StrEnum):
    ID = "id"
    FIRST_CONTACT = "first_contact"
    SCALING_GROUP = "scaling_group"
    SCHEDULABLE = "schedulable"


@strawberry.input(description="Added in 25.18.0. Filter options for agent statuses")
class AgentStatusFilter:
    in_: Optional[list[AgentStatus]] = strawberry.field(name="in", default=None)
    equals: Optional[AgentStatus] = None


@strawberry.input(description="Added in 25.18.0. Filter options for querying agents")
class AgentFilter:
    id: Optional[StringFilter] = None
    status: Optional[AgentStatusFilter] = None
    schedulable: Optional[bool] = None

    AND: Optional[list["AgentFilter"]] = None
    OR: Optional[list["AgentFilter"]] = None
    NOT: Optional[list["AgentFilter"]] = None

    def build_conditions(self) -> list[QueryCondition]:
        field_conditions: list[QueryCondition] = []
        if self.id is not None:
            name_condition = self.id.build_query_condition(
                contains_factory=AgentConditions.by_id_contains,
                equals_factory=AgentConditions.by_id_equals,
            )
            if name_condition is not None:
                field_conditions.append(name_condition)
        if self.status is not None:
            if self.status.in_ is not None:
                field_conditions.append(AgentConditions.by_status_contains(self.status.in_))
            if self.status.equals is not None:
                field_conditions.append(AgentConditions.by_status_equals(self.status.equals))
        if self.schedulable is not None:
            field_conditions.append(AgentConditions.by_schedulable(self.schedulable))

        if self.AND:
            for sub_filter in self.AND:
                field_conditions.extend(sub_filter.build_conditions())

        # Handle OR logical operator
        if self.OR:
            or_sub_conditions: list[QueryCondition] = []
            for sub_filter in self.OR:
                or_sub_conditions.extend(sub_filter.build_conditions())
            if or_sub_conditions:
                field_conditions.append(combine_conditions_or(or_sub_conditions))

        # Handle NOT logical operator
        if self.NOT:
            not_sub_conditions: list[QueryCondition] = []
            for sub_filter in self.NOT:
                not_sub_conditions.extend(sub_filter.build_conditions())
            if not_sub_conditions:
                field_conditions.append(negate_conditions(not_sub_conditions))

        return field_conditions


@strawberry.input(description="Added in 25.18.0. Options for ordering agents")
class AgentOrderBy:
    field: AgentOrderField
    direction: OrderDirection = OrderDirection.ASC

    def to_query_order(self) -> QueryOrder:
        ascending = self.direction == OrderDirection.ASC
        match self.field:
            case AgentOrderField.ID:
                return AgentOrders.id(ascending)
            case AgentOrderField.FIRST_CONTACT:
                return AgentOrders.first_contact(ascending)
            case AgentOrderField.SCALING_GROUP:
                return AgentOrders.scaling_group(ascending)
            case AgentOrderField.SCHEDULABLE:
                return AgentOrders.schedulable(ascending)


@strawberry.type(description="Added in 25.15.0")
class AgentResource:
    capacity: JSON = strawberry.field(
        description="Total amount of resources available in the Agent"
    )
    used: JSON = strawberry.field(
        description="Total amount of resources used in the Agent. It is sum of requested resources for running compute session and already allocated resources for compute sessions."
    )
    free: JSON = strawberry.field(
        description="Total amount of free resources(capacity - used) in the Agent."
    )


@strawberry.type(description="Added in 25.15.0")
class AgentStats:
    total_resource: AgentResource = strawberry.field(description="Added in 25.15.0")


@strawberry.type(description="Added in 25.18.0. Status and lifecycle information for an agent")
class AgentStatusInfo:
    status: AgentStatus = strawberry.field(description="Current status of the agent")
    status_changed: datetime = strawberry.field(
        description="Timestamp when the status last changed"
    )
    first_contact: datetime = strawberry.field(
        description="Timestamp when the agent first made contact"
    )
    lost_at: Optional[datetime] = strawberry.field(
        description="Timestamp when the agent was lost, if applicable"
    )
    schedulable: bool = strawberry.field(description="Indicates if the agent is schedulable")


@strawberry.type(description="Added in 25.18.0. System and configuration information for an agent")
class AgentSystemInfo:
    architecture: str = strawberry.field(description="System architecture of the agent")
    version: str = strawberry.field(description="Version of the agent software")
    auto_terminate_abusing_kernel: bool = strawberry.field(
        description="Not used anymore, present for schema consistency."
    )
    compute_plugins: JSON = strawberry.field(
        description="List of compute plugins supported by the agent"
    )


@strawberry.type(description="Added in 25.18.0. Network-related information for an agent")
class AgentNetworkInfo:
    region: str = strawberry.field(description="Region where the agent is located")
    addr: str = strawberry.field(
        description="Agent's address with port. (bind/advertised host:port)"
    )


@strawberry.type(description="Added in 25.18.0. Strawberry-based Agent type replacing AgentNode.")
class AgentV2(Node):
    id: NodeID[str]
    resource_info: AgentResource
    status_info: AgentStatusInfo
    system_info: AgentSystemInfo
    network_info: AgentNetworkInfo
    permissions: list[AgentPermission] = strawberry.field(
        description="Permissions the current user has on this agent"
    )
    scaling_group: str = strawberry.field(description="Scaling group of the agent")
