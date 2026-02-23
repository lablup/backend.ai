"""Type definitions for Resource Slot DTOs."""

from __future__ import annotations

from enum import StrEnum

from pydantic import Field

from ai.backend.common.api_handlers import BaseRequestModel
from ai.backend.common.dto.manager.query import StringFilter, UUIDFilter

__all__ = (
    "OrderDirection",
    # Agent Resource
    "AgentResourceOrderField",
    "AgentResourceFilter",
    "AgentResourceOrder",
    # Resource Allocation
    "ResourceAllocationOrderField",
    "ResourceAllocationFilter",
    "ResourceAllocationOrder",
)


class OrderDirection(StrEnum):
    ASC = "asc"
    DESC = "desc"


class AgentResourceOrderField(StrEnum):
    AGENT_ID = "agent_id"
    SLOT_NAME = "slot_name"
    CAPACITY = "capacity"
    USED = "used"


class AgentResourceFilter(BaseRequestModel):
    agent_id: StringFilter | None = Field(default=None, description="Filter by agent ID")
    slot_name: StringFilter | None = Field(default=None, description="Filter by slot name")


class AgentResourceOrder(BaseRequestModel):
    field: AgentResourceOrderField = Field(description="Field to order by")
    direction: OrderDirection = Field(default=OrderDirection.ASC, description="Order direction")


class ResourceAllocationOrderField(StrEnum):
    KERNEL_ID = "kernel_id"
    SLOT_NAME = "slot_name"
    REQUESTED = "requested"
    USED = "used"


class ResourceAllocationFilter(BaseRequestModel):
    kernel_id: UUIDFilter | None = Field(default=None, description="Filter by kernel ID")
    slot_name: StringFilter | None = Field(default=None, description="Filter by slot name")


class ResourceAllocationOrder(BaseRequestModel):
    field: ResourceAllocationOrderField = Field(description="Field to order by")
    direction: OrderDirection = Field(default=OrderDirection.ASC, description="Order direction")
