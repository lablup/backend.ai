"""
Pydantic types for Streaming domain.

Covers WebSocket PTY, code execution, TCP/HTTP proxy, and SSE event message types
from the manager's stream, wsproxy, and events APIs.
"""

from __future__ import annotations

from enum import StrEnum
from typing import Annotated, Any, Literal
from uuid import UUID

from pydantic import AliasChoices, BaseModel, ConfigDict, Field

__all__ = (
    # Enums
    "PtyInputMessageType",
    "PtyOutputMessageType",
    "ExecuteMode",
    "ExecuteResultStatus",
    "ServiceProtocol",
    "SessionEventScope",
    "BgtaskSSEEventName",
    # PTY WebSocket messages
    "PtyStdinMessage",
    "PtyResizeMessage",
    "PtyPingMessage",
    "PtyRestartMessage",
    "PtyClientMessage",
    "PtyOutputMessage",
    # Execute WebSocket messages
    "ExecuteRequest",
    "ExecuteResult",
    # Proxy / App
    "StreamProxyParams",
    "StreamAppInfo",
    # SSE event params
    "SessionEventParams",
    "BackgroundTaskEventParams",
    # SSE event payloads
    "BgtaskUpdatedPayload",
    "BgtaskDonePayload",
    "BgtaskPartialSuccessPayload",
    "BgtaskCancelledPayload",
    "BgtaskFailedPayload",
)


# ============================
# Enums
# ============================


class PtyInputMessageType(StrEnum):
    """Client-to-server PTY WebSocket message types."""

    STDIN = "stdin"
    RESIZE = "resize"
    PING = "ping"
    RESTART = "restart"


class PtyOutputMessageType(StrEnum):
    """Server-to-client PTY WebSocket message types."""

    OUT = "out"


class ExecuteMode(StrEnum):
    """Code execution modes."""

    QUERY = "query"
    BATCH = "batch"


class ExecuteResultStatus(StrEnum):
    """Status values in execute result messages."""

    WAITING_INPUT = "waiting-input"
    FINISHED = "finished"
    ERROR = "error"
    SERVER_RESTARTING = "server-restarting"


class ServiceProtocol(StrEnum):
    """Supported service proxy protocols."""

    TCP = "tcp"
    HTTP = "http"
    PREOPEN = "preopen"
    VNC = "vnc"
    RDP = "rdp"


class SessionEventScope(StrEnum):
    """SSE event subscription scope."""

    SESSION = "session"
    KERNEL = "kernel"


class BgtaskSSEEventName(StrEnum):
    """Background task SSE event names."""

    BGTASK_UPDATED = "bgtask_updated"
    BGTASK_DONE = "bgtask_done"
    BGTASK_CANCELLED = "bgtask_cancelled"
    BGTASK_FAILED = "bgtask_failed"


# ============================
# PTY WebSocket Messages
# ============================


class PtyStdinMessage(BaseModel):
    """Client→server: terminal input data (base64-encoded)."""

    model_config = ConfigDict(extra="forbid")

    type: Literal[PtyInputMessageType.STDIN]
    chars: str


class PtyResizeMessage(BaseModel):
    """Client→server: terminal resize event."""

    model_config = ConfigDict(extra="forbid")

    type: Literal[PtyInputMessageType.RESIZE]
    rows: int
    cols: int


class PtyPingMessage(BaseModel):
    """Client→server: keepalive ping."""

    model_config = ConfigDict(extra="forbid")

    type: Literal[PtyInputMessageType.PING]


class PtyRestartMessage(BaseModel):
    """Client→server: kernel restart request."""

    model_config = ConfigDict(extra="forbid")

    type: Literal[PtyInputMessageType.RESTART]


PtyClientMessage = Annotated[
    PtyStdinMessage | PtyResizeMessage | PtyPingMessage | PtyRestartMessage,
    Field(discriminator="type"),
]
"""Discriminated union of all client-to-server PTY WebSocket messages."""


class PtyOutputMessage(BaseModel):
    """Server→client: terminal output data (base64-encoded)."""

    model_config = ConfigDict(extra="forbid")

    type: Literal[PtyOutputMessageType.OUT]
    data: str


# ============================
# Execute WebSocket Messages
# ============================


class ExecuteRequest(BaseModel):
    """Client→server: first message to start code execution."""

    model_config = ConfigDict(extra="forbid")

    mode: ExecuteMode
    code: str = Field(default="")
    options: dict[str, Any] = Field(default_factory=dict)


class ExecuteResult(BaseModel):
    """Server→client: code execution result message."""

    model_config = ConfigDict(extra="forbid")

    status: str
    console: list[Any] | None = Field(default=None)
    exitCode: int | None = Field(default=None)
    options: dict[str, Any] | None = Field(default=None)
    files: dict[str, Any] | None = Field(default=None)
    msg: str | None = Field(default=None)


# ============================
# Proxy / App Parameters
# ============================


class StreamProxyParams(BaseModel):
    """Parameters for stream_proxy / tcpproxy WebSocket endpoints."""

    model_config = ConfigDict(extra="forbid", populate_by_name=True)

    app: str = Field(
        description="Service name to connect to",
        validation_alias=AliasChoices("app", "service"),
    )
    port: int | None = Field(default=None, ge=1024, le=65535, description="Specific port number")
    envs: str | None = Field(default=None, description="Stringified JSON env vars")
    arguments: str | None = Field(default=None, description="Stringified JSON arguments")


class StreamAppInfo(BaseModel):
    """Information about an available streaming app/service."""

    model_config = ConfigDict(extra="forbid")

    name: str
    protocol: str
    ports: list[int]
    url_template: str | None = Field(default=None)
    allowed_arguments: dict[str, Any] | None = Field(default=None)
    allowed_envs: dict[str, Any] | None = Field(default=None)


# ============================
# SSE Event Parameters
# ============================


class SessionEventParams(BaseModel):
    """Parameters for push_session_events SSE endpoint."""

    model_config = ConfigDict(extra="forbid", populate_by_name=True)

    session_name: str = Field(
        default="*",
        validation_alias=AliasChoices("name", "sessionName", "session_name"),
    )
    owner_access_key: str | None = Field(
        default=None,
        validation_alias=AliasChoices("ownerAccessKey", "owner_access_key"),
    )
    session_id: UUID | None = Field(
        default=None,
        validation_alias=AliasChoices("sessionId", "session_id"),
    )
    group_name: str = Field(
        default="*",
        validation_alias=AliasChoices("group", "groupName", "group_name"),
    )
    scope: str = Field(default="*")


class BackgroundTaskEventParams(BaseModel):
    """Parameters for push_background_task_events SSE endpoint."""

    model_config = ConfigDict(extra="forbid", populate_by_name=True)

    task_id: UUID = Field(
        validation_alias=AliasChoices("task_id", "taskId"),
    )


# ============================
# SSE Event Payloads
# ============================


class BgtaskUpdatedPayload(BaseModel):
    """Payload for bgtask_updated SSE event."""

    model_config = ConfigDict(extra="forbid")

    task_id: str
    message: str
    current_progress: float
    total_progress: float


class BgtaskDonePayload(BaseModel):
    """Payload for bgtask_done SSE event."""

    model_config = ConfigDict(extra="forbid")

    task_id: str
    message: str


class BgtaskPartialSuccessPayload(BaseModel):
    """Payload for bgtask_done SSE event with partial success (includes errors)."""

    model_config = ConfigDict(extra="forbid")

    task_id: str
    message: str
    errors: list[str]


class BgtaskCancelledPayload(BaseModel):
    """Payload for bgtask_cancelled SSE event."""

    model_config = ConfigDict(extra="forbid")

    task_id: str
    message: str


class BgtaskFailedPayload(BaseModel):
    """Payload for bgtask_failed SSE event."""

    model_config = ConfigDict(extra="forbid")

    task_id: str
    message: str
