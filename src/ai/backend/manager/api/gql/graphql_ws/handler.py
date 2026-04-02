"""graphql-transport-ws protocol handler for Strawberry GraphQL subscriptions.

Implements the `graphql-transport-ws`_ WebSocket sub-protocol on top of
aiohttp so that Strawberry subscription resolvers can stream events to
clients (including the Hive Gateway).

.. _graphql-transport-ws: https://github.com/enisdenjo/graphql-ws/blob/master/PROTOCOL.md
"""

from __future__ import annotations

import logging
from typing import TYPE_CHECKING, Final

from aiohttp import web

from ai.backend.logging import BraceStyleAdapter
from ai.backend.manager.dto.context import RequestCtx

from .connection import GraphQLWSConnection
from .subscriptions import SubscriptionExecutor
from .types import (
    ClientCompleteMessage,
    PingMessage,
    PongMessage,
    SubscribeMessage,
)

if TYPE_CHECKING:
    from strawberry.federation import Schema as StrawberrySchema

    from ai.backend.manager.api.rest.types import GQLContextDeps

log: Final = BraceStyleAdapter(logging.getLogger(__spec__.name))

_DEFAULT_CONNECTION_INIT_TIMEOUT: Final = 10.0  # seconds


class GraphQLTransportWSHandler:
    """Manages a single WebSocket connection using the *graphql-transport-ws* protocol.

    One instance is created at application startup and reused across connections.
    Per-connection state (active subscriptions) lives entirely inside ``handle()``.
    """

    def __init__(
        self,
        schema: StrawberrySchema,
        gql_deps: GQLContextDeps,
        *,
        max_msg_size: int,
        connection_init_timeout: float = _DEFAULT_CONNECTION_INIT_TIMEOUT,
    ) -> None:
        self._schema = schema
        self._gql_deps = gql_deps
        self._max_msg_size = max_msg_size
        self._connection_init_timeout = connection_init_timeout

    # ------------------------------------------------------------------
    # Public entry point
    # ------------------------------------------------------------------

    async def handle(self, request_ctx: RequestCtx) -> web.WebSocketResponse:
        conn = await GraphQLWSConnection.open(request_ctx.request, max_msg_size=self._max_msg_size)

        if not await conn.wait_connection_init(wait_seconds=self._connection_init_timeout):
            return conn.handler_return

        sender = conn.sender
        receiver = conn.receiver
        subs = SubscriptionExecutor(sender, self._schema, self._gql_deps)

        try:
            async for message in receiver:
                match message:
                    case SubscribeMessage():
                        await subs.start(message)
                    case ClientCompleteMessage():
                        subs.cancel(message)
                    case PingMessage() | PongMessage():
                        await sender.send_pong()
        except Exception as e:
            log.exception("GQL WS: unexpected error ({})", repr(e))
        finally:
            await subs.cancel_all()
        return conn.handler_return
