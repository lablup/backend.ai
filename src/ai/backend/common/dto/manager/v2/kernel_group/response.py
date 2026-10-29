"""
Response DTOs for KernelGroup v2 API.
Shared between Client SDK and Manager API.
"""

from __future__ import annotations

from datetime import datetime
from uuid import UUID

from pydantic import Field

from ai.backend.common.api_handlers import BaseResponseModel
from ai.backend.common.dto.manager.v2.common import BinarySizeInfo

__all__ = (
    "KernelGroupNode",
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
