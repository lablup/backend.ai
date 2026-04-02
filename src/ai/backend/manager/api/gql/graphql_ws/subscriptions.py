"""Per-connection subscription executor."""

from __future__ import annotations

import asyncio
import logging
from typing import TYPE_CHECKING, Final

from strawberry.types.execution import ExecutionResult, PreExecutionError

from ai.backend.logging import BraceStyleAdapter
from ai.backend.manager.api.gql.types import StrawberryGQLContext

from .connection import WSSender
from .types import ClientCompleteMessage, SubscribeMessage, SubscribePayload

if TYPE_CHECKING:
    from strawberry.federation import Schema as StrawberrySchema

    from ai.backend.manager.api.rest.types import GQLContextDeps

log: Final = BraceStyleAdapter(logging.getLogger(__spec__.name))


class SubscriptionExecutor:
    """Executes and manages active subscriptions for a single WebSocket connection.

    Owns the ``WSSender`` for streaming results and handles the full
    subscription lifecycle: start → stream events → complete/error.

    Created per-connection inside ``GraphQLTransportWSHandler.handle()``
    and discarded when the connection closes.
    """

    def __init__(
        self,
        sender: WSSender,
        schema: StrawberrySchema,
        gql_deps: GQLContextDeps,
    ) -> None:
        self._sender = sender
        self._schema = schema
        self._gql_deps = gql_deps
        self._tasks: dict[str, asyncio.Task[None]] = {}

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

    async def start(self, msg: SubscribeMessage) -> None:
        """Start a new subscription.

        If the subscription ID is already active, closes the connection with
        a duplicate-subscriber error (4409) per the protocol spec.
        """
        if msg.id in self._tasks:
            await self._sender.close_duplicate_subscriber()
            return
        self._tasks[msg.id] = asyncio.create_task(self._run(msg.id, msg.payload))

    def cancel(self, msg: ClientCompleteMessage) -> None:
        """Cancel and remove the subscription (client-initiated complete)."""
        if msg.id in self._tasks:
            self._tasks.pop(msg.id).cancel()

    async def cancel_all(self) -> None:
        """Cancel every active subscription and wait for all tasks to finish."""
        for task in self._tasks.values():
            task.cancel()
        await asyncio.gather(*self._tasks.values(), return_exceptions=True)
        self._tasks.clear()

    # ------------------------------------------------------------------
    # Subscription execution
    # ------------------------------------------------------------------

    async def _run(self, sub_id: str, payload: SubscribePayload) -> None:
        sender = self._sender
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
                if sender.closed:
                    break
                match item:
                    case PreExecutionError():
                        await sender.send_pre_execution_error(sub_id, item)
                        return
                    case ExecutionResult():
                        await sender.send_next(sub_id, item)
        except asyncio.CancelledError:
            # Client-initiated complete — do NOT echo complete back.
            send_complete = False
            return
        except Exception as e:
            log.exception("GQL WS: subscription {} error ({})", sub_id, repr(e))
            if not sender.closed:
                await sender.send_internal_error(sub_id)
        finally:
            self._tasks.pop(sub_id, None)
            if send_complete and not sender.closed:
                await sender.send_complete(sub_id)
