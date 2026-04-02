"""graphql-transport-ws protocol message DTOs.

Pydantic models for all client→server and server→client messages
defined by the `graphql-transport-ws`_ sub-protocol.

.. _graphql-transport-ws: https://github.com/enisdenjo/graphql-ws/blob/master/PROTOCOL.md
"""

from __future__ import annotations

import enum
from typing import Annotated, Any, Literal

from pydantic import BaseModel, Field


class GQLWSMessageType(enum.StrEnum):
    # Client → Server
    CONNECTION_INIT = "connection_init"
    SUBSCRIBE = "subscribe"
    COMPLETE = "complete"
    PING = "ping"
    PONG = "pong"
    # Server → Client
    CONNECTION_ACK = "connection_ack"
    NEXT = "next"
    ERROR = "error"


# --- Client → Server ---


class ConnectionInitMessage(BaseModel, frozen=True):
    type: Literal[GQLWSMessageType.CONNECTION_INIT]
    payload: dict[str, Any] | None = None


class SubscribePayload(BaseModel, frozen=True):
    query: str
    variables: dict[str, Any] | None = None
    operationName: str | None = None


class SubscribeMessage(BaseModel, frozen=True):
    type: Literal[GQLWSMessageType.SUBSCRIBE]
    id: str
    payload: SubscribePayload


class ClientCompleteMessage(BaseModel, frozen=True):
    type: Literal[GQLWSMessageType.COMPLETE]
    id: str


class PingMessage(BaseModel, frozen=True):
    type: Literal[GQLWSMessageType.PING] = GQLWSMessageType.PING
    payload: dict[str, Any] | None = None


class PongMessage(BaseModel, frozen=True):
    type: Literal[GQLWSMessageType.PONG] = GQLWSMessageType.PONG
    payload: dict[str, Any] | None = None


# --- Server → Client ---


class ConnectionAckMessage(BaseModel, frozen=True):
    type: Literal[GQLWSMessageType.CONNECTION_ACK] = GQLWSMessageType.CONNECTION_ACK
    payload: dict[str, Any] | None = None


class NextPayload(BaseModel, frozen=True):
    data: dict[str, Any] | None = None
    errors: list[dict[str, Any]] | None = None


class NextMessage(BaseModel, frozen=True):
    type: Literal[GQLWSMessageType.NEXT] = GQLWSMessageType.NEXT
    id: str
    payload: NextPayload


class ErrorMessage(BaseModel, frozen=True):
    type: Literal[GQLWSMessageType.ERROR] = GQLWSMessageType.ERROR
    id: str
    payload: list[dict[str, Any]]


class ServerCompleteMessage(BaseModel, frozen=True):
    type: Literal[GQLWSMessageType.COMPLETE] = GQLWSMessageType.COMPLETE
    id: str


# --- Discriminated union for client messages (post-init phase) ---

ClientMessage = Annotated[
    SubscribeMessage | ClientCompleteMessage | PingMessage | PongMessage,
    Field(discriminator="type"),
]

ServerMessage = (
    ConnectionAckMessage | NextMessage | ErrorMessage | ServerCompleteMessage | PongMessage
)
