"""graphql-transport-ws protocol handler for Strawberry GraphQL subscriptions.

Implements the `graphql-transport-ws`_ WebSocket sub-protocol on top of
aiohttp so that Strawberry subscription resolvers can stream events to
clients (including the Hive Gateway).

.. _graphql-transport-ws: https://github.com/enisdenjo/graphql-ws/blob/master/PROTOCOL.md
"""

from __future__ import annotations

import asyncio
import logging
from collections.abc import AsyncIterator
from typing import TYPE_CHECKING, Any, Final, cast

from aiohttp import WSMsgType, web
from graphql.execution import ExecutionResult

from ai.backend.logging import BraceStyleAdapter

from .types import StrawberryGQLContext

if TYPE_CHECKING:
    from strawberry.federation import Schema as StrawberrySchema

    from ai.backend.manager.api.rest.types import GQLContextDeps

log: Final = BraceStyleAdapter(logging.getLogger(__spec__.name))

_PROTOCOL: Final = "graphql-transport-ws"
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
        ws = web.WebSocketResponse(
            protocols=[_PROTOCOL],
            max_msg_size=self._max_msg_size,
        )
        await ws.prepare(request)

        subscriptions: dict[str, asyncio.Task[None]] = {}

        try:
            if not await self._wait_connection_init(ws):
                return ws

            async for msg in ws:
                if msg.type == WSMsgType.TEXT:
                    await self._handle_message(ws, msg.json(), subscriptions)
                elif msg.type in (WSMsgType.ERROR, WSMsgType.CLOSE):
                    break
        except Exception:
            log.exception("GQL WS: unexpected error")
        finally:
            for task in subscriptions.values():
                task.cancel()
            await asyncio.gather(*subscriptions.values(), return_exceptions=True)
            if not ws.closed:
                await ws.close()
        return ws

    # ------------------------------------------------------------------
    # Protocol helpers
    # ------------------------------------------------------------------

    async def _wait_connection_init(self, ws: web.WebSocketResponse) -> bool:
        try:
            msg = await asyncio.wait_for(ws.receive(), timeout=self._connection_init_timeout)
        except TimeoutError:
            await ws.close(code=4408, message=b"Connection initialisation timeout")
            return False
        if msg.type != WSMsgType.TEXT:
            return False
        data = msg.json()
        if data.get("type") != "connection_init":
            await ws.close(code=4401, message=b"Unauthorized")
            return False
        await ws.send_json({"type": "connection_ack"})
        return True

    async def _handle_message(
        self,
        ws: web.WebSocketResponse,
        data: dict[str, Any],
        subscriptions: dict[str, asyncio.Task[None]],
    ) -> None:
        msg_type = data.get("type")
        msg_id = data.get("id")

        if msg_type == "subscribe" and msg_id is not None:
            if msg_id in subscriptions:
                await ws.close(code=4409, message=b"Subscriber already exists")
                return
            payload = data.get("payload", {})
            task = asyncio.create_task(
                self._run_subscription(ws, msg_id, payload, subscriptions),
            )
            subscriptions[msg_id] = task

        elif msg_type == "complete" and msg_id is not None:
            if msg_id in subscriptions:
                subscriptions.pop(msg_id).cancel()

        elif msg_type == "ping":
            await ws.send_json({"type": "pong"})

    # ------------------------------------------------------------------
    # Subscription execution
    # ------------------------------------------------------------------

    async def _run_subscription(
        self,
        ws: web.WebSocketResponse,
        sub_id: str,
        payload: dict[str, Any],
        subscriptions: dict[str, asyncio.Task[None]],
    ) -> None:
        gql_ctx = self._make_gql_context()
        send_complete = True
        try:
            result = await self._schema.subscribe(
                payload.get("query", ""),
                variable_values=payload.get("variables"),
                operation_name=payload.get("operationName"),
                context_value=gql_ctx,
            )
            if isinstance(result, ExecutionResult):
                # Subscription resolver returned an error (not an iterator).
                errors = [dict(e.formatted) for e in result.errors] if result.errors else []
                await ws.send_json({
                    "id": sub_id,
                    "type": "error",
                    "payload": errors,
                })
                return

            result_iter = cast(AsyncIterator[ExecutionResult], result)
            try:
                async for item in result_iter:
                    if ws.closed:
                        break
                    resp: dict[str, Any] = {"id": sub_id, "type": "next", "payload": {}}
                    if item.data is not None:
                        resp["payload"]["data"] = item.data
                    if item.errors:
                        resp["payload"]["errors"] = [dict(e.formatted) for e in item.errors]
                    await ws.send_json(resp)
            finally:
                if hasattr(result_iter, "aclose"):
                    await result_iter.aclose()
        except asyncio.CancelledError:
            # Client-initiated complete — do NOT echo complete back.
            send_complete = False
            return
        except Exception:
            log.exception("GQL WS: subscription {} error", sub_id)
            if not ws.closed:
                await ws.send_json({
                    "id": sub_id,
                    "type": "error",
                    "payload": [{"message": "Internal server error"}],
                })
        finally:
            subscriptions.pop(sub_id, None)
            if send_complete and not ws.closed:
                await ws.send_json({"id": sub_id, "type": "complete"})
