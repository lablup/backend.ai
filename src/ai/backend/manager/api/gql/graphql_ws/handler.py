"""graphql-transport-ws protocol handler for Strawberry GraphQL subscriptions.

Implements the `graphql-transport-ws`_ WebSocket sub-protocol on top of
aiohttp so that Strawberry subscription resolvers can stream events to
clients (including the Hive Gateway).

.. _graphql-transport-ws: https://github.com/enisdenjo/graphql-ws/blob/master/PROTOCOL.md
"""

from __future__ import annotations

import asyncio
import logging
from typing import TYPE_CHECKING, Final

from aiohttp import web
from strawberry.types.execution import PreExecutionError

from ai.backend.logging import BraceStyleAdapter
from ai.backend.manager.api.gql.types import StrawberryGQLContext

from .connection import GraphQLWSConnection
from .subscriptions import SubscriptionRegistry
from .types import (
    ClientCompleteMessage,
    PingMessage,
    PongMessage,
    SubscribeMessage,
    SubscribePayload,
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

    def _make_gql_context(self) -> StrawberryGQLContext:
        deps = self._gql_deps
        return StrawberryGQLContext(
            config_provider=deps.config_provider,
            event_hub=deps.processors.events.event_hub,
            event_fetcher=deps.processors.events.event_fetcher,
            gql_adapter=deps.strawberry_gql_adapter,
            data_loaders=deps.strawberry_data_loaders,
            metric_observer=deps.metric_observer,
            adapters=deps.adapters,
        )

    # ------------------------------------------------------------------
    # Public entry point
    # ------------------------------------------------------------------

    async def handle(self, request: web.Request) -> web.WebSocketResponse:
        conn = await GraphQLWSConnection.open(request, max_msg_size=self._max_msg_size)
        subs = SubscriptionRegistry()

        try:
            if not await self._wait_connection_init(conn):
                return conn.raw

            async for message in conn:
                match message:
                    case SubscribeMessage():
                        started = subs.start(
                            message.id,
                            self._run_subscription(conn, message.id, message.payload, subs),
                        )
                        if not started:
                            await conn.close_duplicate_subscriber()
                    case ClientCompleteMessage():
                        subs.cancel(message.id)
                    case PingMessage() | PongMessage():
                        await conn.send_pong()
        except Exception:
            log.exception("GQL WS: unexpected error")
        finally:
            await subs.cancel_all()
            await conn.close()
        return conn.raw

    # ------------------------------------------------------------------
    # Protocol helpers
    # ------------------------------------------------------------------

    async def _wait_connection_init(self, conn: GraphQLWSConnection) -> bool:
        received = await conn.receive_init(wait_seconds=self._connection_init_timeout)
        if not received:
            await conn.close_init_timeout()
            return False
        await conn.send_ack()
        return True

    # ------------------------------------------------------------------
    # Subscription execution
    # ------------------------------------------------------------------

    async def _run_subscription(
        self,
        conn: GraphQLWSConnection,
        sub_id: str,
        payload: SubscribePayload,
        subs: SubscriptionRegistry,
    ) -> None:
        gql_ctx = self._make_gql_context()
        send_complete = True
        try:
            result_stream = await self._schema.subscribe(
                payload.query,
                variable_values=payload.variables,
                operation_name=payload.operationName,
                context_value=gql_ctx,
            )
            async for item in result_stream:
                if conn.closed:
                    break
                if isinstance(item, PreExecutionError):
                    await conn.send_pre_execution_error(sub_id, item)
                    return
                await conn.send_next(sub_id, item)
        except asyncio.CancelledError:
            # Client-initiated complete — do NOT echo complete back.
            send_complete = False
            return
        except Exception:
            log.exception("GQL WS: subscription {} error", sub_id)
            if not conn.closed:
                await conn.send_internal_error(sub_id)
        finally:
            subs.remove(sub_id)
            if send_complete and not conn.closed:
                await conn.send_complete(sub_id)
