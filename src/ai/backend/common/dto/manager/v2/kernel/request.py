"""Request DTOs for kernel DTO v2."""

from __future__ import annotations

from pydantic import Field

from ai.backend.common.api_handlers import BaseRequestModel
from ai.backend.common.dto.manager.query import UUIDFilter

from .types import KernelOrderField, OrderDirection

__all__ = (
    "AdminSearchKernelsInput",
    "KernelFilter",
    "KernelOrder",
)


class KernelFilter(BaseRequestModel):
    """Filter conditions for kernel search."""

    id: UUIDFilter | None = Field(default=None, description="Filter by kernel ID")
    session_id: UUIDFilter | None = Field(default=None, description="Filter by session ID")
    # Add status filter if KernelStatusFilter enum is available
    # For now keep it minimal


class KernelOrder(BaseRequestModel):
    """Order specification for kernel search."""

    field: KernelOrderField = Field(description="Field to order by")
    direction: OrderDirection = Field(default=OrderDirection.DESC, description="Order direction")


class AdminSearchKernelsInput(BaseRequestModel):
    """Input for admin search of kernels."""

    filter: KernelFilter | None = Field(default=None, description="Filter conditions")
    order: list[KernelOrder] | None = Field(default=None, description="Order specifications")
    first: int | None = Field(default=None, description="Cursor pagination: number of items")
    after: str | None = Field(default=None, description="Cursor pagination: after cursor")
    last: int | None = Field(default=None, description="Cursor pagination: last N items")
    before: str | None = Field(default=None, description="Cursor pagination: before cursor")
    limit: int | None = Field(default=None, description="Offset pagination: maximum items")
    offset: int | None = Field(default=None, description="Offset pagination: number to skip")
