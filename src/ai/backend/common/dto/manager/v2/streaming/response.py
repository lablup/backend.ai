"""
Response DTOs for Streaming domain (v2).

These Node/Payload models represent the JSON payloads exchanged over PTY WebSocket,
execute WebSocket, and the streaming-apps REST endpoint.

Unlike the v1 models, these use canonical snake_case field names with no camelCase aliases.
"""

from __future__ import annotations

from typing import Any, Literal

from pydantic import Field

from ai.backend.common.api_handlers import BaseResponseModel
from ai.backend.common.dto.manager.v2.streaming.types import (
    PtyOutputMessageType,
    StreamAppInfoNode,
)

__all__ = (
    "ExecuteResultNode",
    "GetStreamAppsPayload",
    "PtyOutputNode",
)


class PtyOutputNode(BaseResponseModel):
    """Node model for server-to-client PTY WebSocket output messages."""

    type: Literal[PtyOutputMessageType.OUT]
    data: str = Field(description="Terminal output data (base64-encoded)")


class ExecuteResultNode(BaseResponseModel):
    """Node model for server-to-client code execution result messages."""

    status: str = Field(description="Execution status")
    console: list[Any] | None = Field(default=None, description="Console output entries")
    exit_code: int | None = Field(default=None, description="Process exit code")
    options: dict[str, Any] | None = Field(
        default=None, description="Additional execution options returned by the kernel"
    )
    files: dict[str, Any] | None = Field(
        default=None, description="Output files produced by the execution"
    )
    msg: str | None = Field(default=None, description="Human-readable status message")


class GetStreamAppsPayload(BaseResponseModel):
    """Payload for listing available streaming apps/services."""

    apps: list[StreamAppInfoNode] = Field(description="List of available streaming apps")
