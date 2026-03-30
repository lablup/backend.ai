"""
Request DTOs for streaming DTO v2.

Covers PTY WebSocket messages, code execution, and stream proxy inputs.
"""

from __future__ import annotations

from typing import Annotated, Any, Literal

from pydantic import Field

from ai.backend.common.api_handlers import BaseRequestModel

from .types import ExecuteMode, PtyInputMessageType

__all__ = (
    "PtyStdinInput",
    "PtyResizeInput",
    "PtyPingInput",
    "PtyRestartInput",
    "PtyClientInput",
    "ExecuteInput",
    "StreamProxyInput",
)


class PtyStdinInput(BaseRequestModel):
    """Client→server: terminal input data (base64-encoded)."""

    type: Literal[PtyInputMessageType.STDIN]
    chars: str = Field(description="Input characters to send to the terminal")


class PtyResizeInput(BaseRequestModel):
    """Client→server: terminal resize event."""

    type: Literal[PtyInputMessageType.RESIZE]
    rows: int = Field(description="Number of rows in the terminal")
    cols: int = Field(description="Number of columns in the terminal")


class PtyPingInput(BaseRequestModel):
    """Client→server: keepalive ping."""

    type: Literal[PtyInputMessageType.PING]


class PtyRestartInput(BaseRequestModel):
    """Client→server: kernel restart request."""

    type: Literal[PtyInputMessageType.RESTART]


PtyClientInput = Annotated[
    PtyStdinInput | PtyResizeInput | PtyPingInput | PtyRestartInput,
    Field(discriminator="type"),
]
"""Discriminated union of all client-to-server PTY WebSocket messages."""


class ExecuteInput(BaseRequestModel):
    """Input for code execution over WebSocket."""

    mode: ExecuteMode = Field(description="Execution mode: query or batch")
    code: str = Field(default="", description="Code to execute")
    options: dict[str, Any] = Field(
        default_factory=dict, description="Additional execution options"
    )


class StreamProxyInput(BaseRequestModel):
    """Input for stream proxy / tcpproxy WebSocket endpoints."""

    app: str = Field(description="Service name to connect to")
    port: int | None = Field(
        default=None,
        ge=1024,
        le=65535,
        description="Specific port number (1024-65535)",
    )
    envs: str | None = Field(default=None, description="Stringified JSON env vars")
    arguments: str | None = Field(default=None, description="Stringified JSON arguments")
