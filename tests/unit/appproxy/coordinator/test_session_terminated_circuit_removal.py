from __future__ import annotations

import uuid
from collections.abc import Awaitable, Callable
from unittest.mock import AsyncMock, MagicMock, patch

from ai.backend.appproxy.coordinator import server
from ai.backend.appproxy.coordinator.models import Circuit
from ai.backend.common.events.event_types.session.broadcast import SchedulingBroadcastEvent
from ai.backend.common.types import SessionId


def make_event(status_transition: str = "TERMINATED") -> SchedulingBroadcastEvent:
    return SchedulingBroadcastEvent(
        session_id=SessionId(uuid.uuid4()),
        creation_id="",
        status_transition=status_transition,
        reason="user-requested",
    )


async def run_handler(
    circuits: list[MagicMock],
    event: SchedulingBroadcastEvent,
) -> tuple[MagicMock, MagicMock]:
    root_ctx = MagicMock()
    root_ctx.circuit_manager.unload_circuits = AsyncMock()
    sess = MagicMock(delete=AsyncMock())

    async def run_txn(txn: Callable[..., Awaitable[object]], *_args: object) -> object:
        return await txn(sess)

    with (
        patch.object(Circuit, "list_interactive_by_session", AsyncMock(return_value=circuits)),
        patch.object(server, "execute_with_txn_retry", run_txn),
    ):
        await server.on_session_terminated_event(root_ctx, MagicMock(), event)
    return root_ctx, sess


class TestSessionTerminatedCircuitRemoval:
    async def test_removes_and_unloads_circuits_of_the_session(self) -> None:
        circuits = [MagicMock(spec=Circuit), MagicMock(spec=Circuit)]
        for circuit in circuits:
            circuit.worker_row = MagicMock(occupied_slots=3)

        root_ctx, sess = await run_handler(circuits, make_event())

        assert [call.args[0] for call in sess.delete.await_args_list] == circuits
        assert all(c.worker_row.occupied_slots == 2 for c in circuits)
        root_ctx.circuit_manager.unload_circuits.assert_awaited_once_with(circuits)

    async def test_does_nothing_without_circuits(self) -> None:
        root_ctx, sess = await run_handler([], make_event())

        sess.delete.assert_not_awaited()
        root_ctx.circuit_manager.unload_circuits.assert_not_awaited()

    async def test_ignores_other_status_transitions(self) -> None:
        circuits = [MagicMock(spec=Circuit)]

        root_ctx, sess = await run_handler(circuits, make_event("TERMINATING"))

        sess.delete.assert_not_awaited()
        root_ctx.circuit_manager.unload_circuits.assert_not_awaited()

    async def test_is_subscribed_to_scheduling_events(self) -> None:
        root_ctx = MagicMock()

        async with server.event_handler_ctx(root_ctx):
            subscribe = root_ctx.core_event_dispatcher.subscribe
            assert subscribe.call_args.args[0] is SchedulingBroadcastEvent
            assert subscribe.call_args.args[2] is server.on_session_terminated_event
