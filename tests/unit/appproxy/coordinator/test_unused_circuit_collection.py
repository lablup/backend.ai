from __future__ import annotations

import time
import uuid
from collections.abc import Awaitable, Callable
from datetime import UTC, datetime, timedelta
from unittest.mock import AsyncMock, MagicMock, patch

import pytest

from ai.backend.appproxy.common.types import AppMode, ProxyProtocol
from ai.backend.appproxy.coordinator import server
from ai.backend.appproxy.coordinator.models import Circuit, Worker

TIMEOUT = 3600


def make_circuit(
    protocol: ProxyProtocol,
    app_mode: AppMode,
    *,
    age: float = 2 * TIMEOUT,
) -> MagicMock:
    circuit = MagicMock(spec=Circuit)
    circuit.id = uuid.uuid4()
    circuit.worker = uuid.uuid4()
    circuit.protocol = protocol
    circuit.app_mode = app_mode
    circuit.created_at = datetime.now(UTC) - timedelta(seconds=age)
    return circuit


async def run_collection(
    circuits: list[MagicMock],
    last_access: dict[uuid.UUID, float] | None = None,
    *,
    enable_traefik: bool = False,
) -> list[uuid.UUID]:
    """Run the idle collector once and return the ids of the circuits it unloaded."""
    last_access = last_access or {}
    root_ctx = MagicMock()
    root_ctx.local_config.proxy_coordinator.unused_circuit_collection_timeout = TIMEOUT
    root_ctx.local_config.proxy_coordinator.enable_traefik = enable_traefik
    root_ctx.circuit_manager.unload_circuits = AsyncMock()

    async def get_live_data(keys: list[str]) -> list[bytes | None]:
        by_key = {f"circuit.{cid}.last_access": str(ts).encode() for cid, ts in last_access.items()}
        return [by_key.get(key) for key in keys]

    root_ctx.valkey_live.get_multiple_live_data = get_live_data

    async def run_txn(
        txn: Callable[..., Awaitable[list[MagicMock]]], *_args: object
    ) -> list[MagicMock]:
        return await txn(MagicMock(delete=AsyncMock()))

    worker = MagicMock(occupied_slots=1)
    with (
        patch.object(Circuit, "list_circuits", AsyncMock(return_value=circuits)),
        patch.object(Worker, "get", AsyncMock(return_value=worker)),
        patch.object(server, "execute_with_txn_retry", run_txn),
    ):
        async with server.unused_port_collection_ctx(root_ctx):
            collect = root_ctx.event_dispatcher.consume.call_args.args[2]
            await collect(None, MagicMock(), MagicMock())
    unloaded = root_ctx.circuit_manager.unload_circuits.await_args.args[0]
    return [c.id for c in unloaded]


class TestUnusedCircuitCollection:
    @pytest.mark.parametrize("protocol", [ProxyProtocol.HTTP, ProxyProtocol.TCP])
    async def test_collects_idle_interactive_circuit(self, protocol: ProxyProtocol) -> None:
        circuit = make_circuit(protocol, AppMode.INTERACTIVE)

        collected = await run_collection([circuit])

        assert collected == [circuit.id]

    async def test_keeps_tcp_circuit_with_recent_access(self) -> None:
        circuit = make_circuit(ProxyProtocol.TCP, AppMode.INTERACTIVE)

        collected = await run_collection([circuit], {circuit.id: time.time() - 10})

        assert collected == []

    async def test_keeps_tcp_circuit_younger_than_timeout(self) -> None:
        circuit = make_circuit(ProxyProtocol.TCP, AppMode.INTERACTIVE, age=60)

        collected = await run_collection([circuit])

        assert collected == []

    async def test_collects_tcp_circuit_with_stale_access(self) -> None:
        circuit = make_circuit(ProxyProtocol.TCP, AppMode.INTERACTIVE, age=10 * TIMEOUT)

        collected = await run_collection([circuit], {circuit.id: time.time() - 2 * TIMEOUT})

        assert collected == [circuit.id]

    async def test_keeps_tcp_circuit_with_traefik(self) -> None:
        circuits = [
            make_circuit(ProxyProtocol.TCP, AppMode.INTERACTIVE),
            make_circuit(ProxyProtocol.HTTP, AppMode.INTERACTIVE),
        ]

        collected = await run_collection(circuits, enable_traefik=True)

        assert collected == [circuits[1].id]

    async def test_never_collects_inference_circuit(self) -> None:
        circuits = [
            make_circuit(ProxyProtocol.TCP, AppMode.INFERENCE),
            make_circuit(ProxyProtocol.HTTP, AppMode.INFERENCE),
        ]

        collected = await run_collection(circuits)

        assert collected == []

    @pytest.mark.parametrize("protocol", [ProxyProtocol.HTTP2, ProxyProtocol.GRPC])
    async def test_skips_protocols_without_access_marker(self, protocol: ProxyProtocol) -> None:
        circuit = make_circuit(protocol, AppMode.INTERACTIVE)

        collected = await run_collection([circuit])

        assert collected == []
