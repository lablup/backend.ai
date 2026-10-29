"""
Response DTOs for KernelGroup v2 API.
Shared between Client SDK and Manager API.
"""

from __future__ import annotations

from datetime import datetime
from decimal import Decimal
from uuid import UUID

from pydantic import Field

from ai.backend.common.api_handlers import BaseResponseModel
from ai.backend.common.dto.manager.v2.common import BinarySizeInfo

__all__ = (
    "KernelGroupEnvironNode",
    "KernelGroupNode",
    "KernelGroupResourceSlotNode",
    "ScopedSearchKernelGroupEnvironsPayload",
    "ScopedSearchKernelGroupResourceSlotsPayload",
    "ScopedSearchKernelGroupsPayload",
)


class KernelGroupNode(BaseResponseModel):
    """One role of a session and the execution spec its kernels share."""

    id: UUID = Field(description="ID of the kernel group.")
    field_id: UUID = Field(description="ID of the kernel group.")
    session_id: UUID = Field(description="ID of the session the group belongs to.")
    role: str = Field(description="Role of the group, unique within its session.")
    image_id: UUID | None = Field(
        default=None, description="ID of the image the group's kernels run."
    )
    shmem: BinarySizeInfo | None = Field(
        default=None, description="Shared memory requested for the group. Null means the default."
    )
    startup_command: str | None = Field(
        default=None, description="Command the group's kernels run at startup."
    )
    preopen_ports: list[int] = Field(description="Ports pre-opened on the group's kernels.")
    requested_starts_at: datetime | None = Field(
        default=None,
        description="Reserved start time requested at creation. Honored only for batch sessions.",
    )
    batch_timeout: int | None = Field(
        default=None, description="Batch execution timeout in seconds."
    )


class ScopedSearchKernelGroupsPayload(BaseResponseModel):
    """Payload for paginated kernel group search results."""

    items: list[KernelGroupNode] = Field(description="List of kernel group nodes.")
    total_count: int = Field(description="Total number of kernel groups matching the filter.")
    has_next_page: bool = Field(description="Whether there is a next page.")
    has_previous_page: bool = Field(description="Whether there is a previous page.")


class KernelGroupEnvironNode(BaseResponseModel):
    """One environment variable requested on a kernel group."""

    id: UUID = Field(description="ID of the environ row.")
    field_id: UUID = Field(description="ID of the environ row.")
    kernel_group_id: UUID = Field(description="ID of the kernel group the row belongs to.")
    key: str = Field(description="Variable name.")
    value: str = Field(description="Variable value.")


class ScopedSearchKernelGroupEnvironsPayload(BaseResponseModel):
    """Payload for paginated kernel group environ search results."""

    items: list[KernelGroupEnvironNode] = Field(description="List of environ nodes.")
    total_count: int = Field(description="Total number of environ rows matching the filter.")
    has_next_page: bool = Field(description="Whether there is a next page.")
    has_previous_page: bool = Field(description="Whether there is a previous page.")


class KernelGroupResourceSlotNode(BaseResponseModel):
    """One slot's amount requested on each kernel of a kernel group."""

    id: UUID = Field(description="ID of the resource slot row.")
    field_id: UUID = Field(description="ID of the resource slot row.")
    kernel_group_id: UUID = Field(description="ID of the kernel group the row belongs to.")
    slot_name: str = Field(description="Resource slot name (e.g. cpu, mem).")
    quantity: Decimal = Field(description="Amount requested on each kernel of the group.")


class ScopedSearchKernelGroupResourceSlotsPayload(BaseResponseModel):
    """Payload for paginated kernel group resource slot search results."""

    items: list[KernelGroupResourceSlotNode] = Field(description="List of resource slot nodes.")
    total_count: int = Field(description="Total number of resource slot rows matching the filter.")
    has_next_page: bool = Field(description="Whether there is a next page.")
    has_previous_page: bool = Field(description="Whether there is a previous page.")
