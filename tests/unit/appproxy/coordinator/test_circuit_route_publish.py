"""Tests for atomic etcd publishing of Traefik circuit routes.

Covers CircuitManager's route-update and initialize paths, which must publish
each circuit's config via a single ``atomic_replace_prefixes`` transaction so
Traefik never observes a revision where a router's backing service has briefly
vanished (the cause of dropped requests during route churn).
"""

from __future__ import annotations

from types import SimpleNamespace
from typing import Any, cast
from unittest.mock import AsyncMock, MagicMock
from uuid import uuid4

from ai.backend.appproxy.common.types import ProxyProtocol
from ai.backend.appproxy.coordinator.models import Circuit
from ai.backend.appproxy.coordinator.types import CircuitManager, CircuitRouteUpdateItem


def _make_manager(traefik_etcd: Any) -> CircuitManager:
    return CircuitManager(
        event_dispatcher=cast(Any, MagicMock()),
        event_producer=cast(Any, MagicMock()),
        traefik_etcd=traefik_etcd,
        local_config=cast(
            Any,
            SimpleNamespace(proxy_coordinator=SimpleNamespace(enable_traefik=True)),
        ),
    )


def _make_circuit(
    *,
    authority: str = "worker-1",
    servers: list[dict[str, str]] | None = None,
) -> Circuit:
    circuit: Any = MagicMock(spec=Circuit)
    circuit.id = uuid4()
    circuit.protocol = ProxyProtocol.HTTP
    circuit.worker_row = SimpleNamespace(authority=authority)
    # ``servers=None`` models a circuit with no active routes, whose empty
    # traefik_services tells the publish path to remove the service subtree.
    circuit.traefik_services = (
        {f"bai_service_{circuit.id}": {"loadBalancer": {"servers": servers}}}
        if servers is not None
        else {}
    )
    return cast(Circuit, circuit)


class TestUpdateCircuitRoutesBulk:
    async def test_publishes_single_atomic_replace(self) -> None:
        traefik_etcd = MagicMock()
        traefik_etcd.atomic_replace_prefixes = AsyncMock()
        traefik_etcd.delete_prefix = AsyncMock()
        traefik_etcd.put_prefix = AsyncMock()
        manager = _make_manager(traefik_etcd)

        circuit = _make_circuit(servers=[{"url": "http://h:1/"}])

        await manager.update_circuit_routes_bulk([
            CircuitRouteUpdateItem(circuit=circuit, old_routes=[])
        ])

        # The whole update is one atomic transaction; the old delete-then-put
        # split (which left a routing gap) must be gone.
        assert traefik_etcd.atomic_replace_prefixes.await_count == 1
        assert traefik_etcd.delete_prefix.await_count == 0
        assert traefik_etcd.put_prefix.await_count == 0

        replacements = traefik_etcd.atomic_replace_prefixes.await_args.args[0]
        expected_prefix = f"worker_worker-1/http/services/bai_service_{circuit.id}"
        assert set(replacements.keys()) == {expected_prefix}
        # Server list flattened into index-keyed dict by convert_to_etcd_dict.
        assert replacements[expected_prefix] == {
            "loadBalancer": {"servers": {"0": {"url": "http://h:1/"}}}
        }

    async def test_empty_service_removes_subtree(self) -> None:
        traefik_etcd = MagicMock()
        traefik_etcd.atomic_replace_prefixes = AsyncMock()
        manager = _make_manager(traefik_etcd)

        # No active routes → empty traefik_services → empty replacement body,
        # which atomic_replace_prefixes interprets as "remove the subtree".
        circuit = _make_circuit()

        await manager.update_circuit_routes_bulk([
            CircuitRouteUpdateItem(circuit=circuit, old_routes=[])
        ])

        replacements = traefik_etcd.atomic_replace_prefixes.await_args.args[0]
        expected_prefix = f"worker_worker-1/http/services/bai_service_{circuit.id}"
        assert replacements == {expected_prefix: {}}

    async def test_distinct_circuits_get_distinct_prefixes(self) -> None:
        traefik_etcd = MagicMock()
        traefik_etcd.atomic_replace_prefixes = AsyncMock()
        manager = _make_manager(traefik_etcd)

        c1 = _make_circuit(servers=[])
        c2 = _make_circuit(authority="worker-2", servers=[])

        await manager.update_circuit_routes_bulk([
            CircuitRouteUpdateItem(circuit=c1, old_routes=[]),
            CircuitRouteUpdateItem(circuit=c2, old_routes=[]),
        ])

        replacements = traefik_etcd.atomic_replace_prefixes.await_args.args[0]
        assert set(replacements.keys()) == {
            f"worker_worker-1/http/services/bai_service_{c1.id}",
            f"worker_worker-2/http/services/bai_service_{c2.id}",
        }


class TestInitializeTraefikCircuits:
    async def test_publishes_router_service_middleware_subtrees(self) -> None:
        traefik_etcd = MagicMock()
        traefik_etcd.atomic_replace_prefixes = AsyncMock()
        traefik_etcd.put_prefix = AsyncMock()
        manager = _make_manager(traefik_etcd)

        circuit: Any = MagicMock(spec=Circuit)
        circuit.id = uuid4()
        circuit.protocol = ProxyProtocol.HTTP
        circuit.worker_row = SimpleNamespace(authority="worker-1")
        circuit.traefik_routers = {f"bai_router_{circuit.id}": {"rule": "Host(`x`)"}}
        circuit.traefik_services = {
            f"bai_service_{circuit.id}": {"loadBalancer": {"servers": [{"url": "http://h:1/"}]}}
        }
        circuit.get_traefik_middlewares = MagicMock(
            return_value={
                "CORSHeaders": {"headers": {"accessControlAllowOriginList": ["*"]}},
                f"bai_appproxy_plugin_{circuit.id}": {"plugin": {"p": {"k": "v"}}},
                f"bai_appproxy_plugin_{circuit.id}_go": {"plugin": {"g": {"id": "1"}}},
            }
        )

        await manager.initialize_traefik_circuits([cast(Circuit, circuit)])

        assert traefik_etcd.atomic_replace_prefixes.await_count == 1
        assert traefik_etcd.put_prefix.await_count == 0
        replacements = traefik_etcd.atomic_replace_prefixes.await_args.args[0]
        assert set(replacements.keys()) == {
            f"worker_worker-1/http/routers/bai_router_{circuit.id}",
            f"worker_worker-1/http/services/bai_service_{circuit.id}",
            "worker_worker-1/http/middlewares/CORSHeaders",
            f"worker_worker-1/http/middlewares/bai_appproxy_plugin_{circuit.id}",
            f"worker_worker-1/http/middlewares/bai_appproxy_plugin_{circuit.id}_go",
        }
