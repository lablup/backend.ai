"""
Common types for streaming DTO v2.

Defines streaming-related enums and the StreamAppInfoNode sub-model.
"""

from __future__ import annotations

from enum import StrEnum
from typing import Any

from pydantic import Field

from ai.backend.common.api_handlers import BaseResponseModel

__all__ = (
    "PtyInputMessageType",
    "PtyOutputMessageType",
    "ExecuteMode",
    "ExecuteResultStatus",
    "ServiceProtocol",
    "StreamAppInfoNode",
)


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


class StreamAppInfoNode(BaseResponseModel):
    """Information about an available streaming app/service."""

    name: str
    protocol: str
    ports: list[int]
    url_template: str | None = Field(default=None)
    allowed_arguments: dict[str, Any] | None = Field(default=None)
    allowed_envs: dict[str, Any] | None = Field(default=None)
