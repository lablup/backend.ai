"""Tests for Circuit.traefik_services single-loadBalancer structure.

Verifies:
- A single ``bai_service_{circuit.id}`` entry is emitted (no per-session weighted sub-services).
- ``loadBalancer.servers`` aggregates every route's kernel URL in order.
- ``loadBalancer.healthCheck`` directive is attached once when the endpoint has
  health checking enabled (and only for HTTP inference circuits).
"""

from __future__ import annotations

from typing import Any
from unittest.mock import MagicMock
from uuid import uuid4

from ai.backend.appproxy.common.types import (
    AppMode,
    FrontendMode,
    ProxyProtocol,
    RouteInfo,
)
from ai.backend.appproxy.coordinator.models.circuit import Circuit
from ai.backend.common.config import ModelHealthCheck
from ai.backend.common.types import ModelServiceStatus


def _make_route(kernel_host: str = "127.0.0.1", kernel_port: int = 8000) -> RouteInfo:
    return RouteInfo(
        route_id=uuid4(),
        session_id=uuid4(),
        session_name=None,
        kernel_host=kernel_host,
        kernel_port=kernel_port,
        protocol=ProxyProtocol.HTTP,
        traffic_ratio=1.0,
        health_status=None,
        last_health_check=None,
        consecutive_failures=0,
    )


def _make_inference_circuit(
    *,
    routes: list[RouteInfo],
    protocol: ProxyProtocol = ProxyProtocol.HTTP,
    health_check_enabled: bool = True,
    health_check_config: ModelHealthCheck | None = None,
    app_mode: AppMode = AppMode.INFERENCE,
) -> Circuit:
    circuit = Circuit()
    circuit.id = uuid4()
    circuit.app = "inference"
    circuit.protocol = protocol
    circuit.worker = uuid4()
    circuit.app_mode = app_mode
    circuit.frontend_mode = FrontendMode.PORT
    circuit.port = 10205
    circuit.subdomain = None
    circuit.endpoint_id = uuid4()
    circuit.route_info = routes

    endpoint = MagicMock()
    endpoint.health_check_enabled = health_check_enabled
    endpoint.health_check_config = health_check_config
    circuit.endpoint_row = endpoint

    return circuit


def _default_health_check_config() -> ModelHealthCheck:
    return ModelHealthCheck(
        path="/health",
        interval=10.0,
        max_wait_time=5.0,
    )


class TestCircuitTraefikServicesStructure:
    """Verify the new single-loadBalancer output shape."""

    def test_single_bai_service_entry_only(self) -> None:
        route = _make_route()
        circuit = _make_inference_circuit(
            routes=[route],
            health_check_enabled=False,
            health_check_config=None,
        )

        services = circuit.traefik_services

        # Exactly one top-level key: bai_service_{circuit.id}. No per-session entries.
        assert set(services.keys()) == {f"bai_service_{circuit.id}"}
        assert "loadBalancer" in services[f"bai_service_{circuit.id}"]
        assert "weighted" not in services[f"bai_service_{circuit.id}"]

    def test_servers_list_contains_every_route(self) -> None:
        r1 = _make_route(kernel_host="10.0.0.1", kernel_port=8000)
        r2 = _make_route(kernel_host="10.0.0.2", kernel_port=8001)
        r3 = _make_route(kernel_host="10.0.0.3", kernel_port=8002)
        circuit = _make_inference_circuit(
            routes=[r1, r2, r3],
            health_check_enabled=False,
            health_check_config=None,
        )

        services = circuit.traefik_services
        load_balancer = services[f"bai_service_{circuit.id}"]["loadBalancer"]

        assert load_balancer["servers"] == [
            {"url": "http://10.0.0.1:8000/"},
            {"url": "http://10.0.0.2:8001/"},
            {"url": "http://10.0.0.3:8002/"},
        ]

    def test_empty_route_info_returns_empty_services(self) -> None:
        circuit = _make_inference_circuit(
            routes=[],
            health_check_enabled=True,
            health_check_config=_default_health_check_config(),
        )

        assert circuit.traefik_services == {}


class TestCircuitTraefikServicesHealthCheck:
    """Verify loadBalancer.healthCheck directive is injected appropriately."""

    def test_http_inference_with_health_check_includes_directive(self) -> None:
        route = _make_route()
        circuit = _make_inference_circuit(
            routes=[route],
            health_check_enabled=True,
            health_check_config=_default_health_check_config(),
        )

        services = circuit.traefik_services

        load_balancer: dict[str, Any] = services[f"bai_service_{circuit.id}"]["loadBalancer"]
        assert load_balancer["healthCheck"] == {
            "path": "/health",
            "interval": "10s",
            "timeout": "5s",
        }
        # Servers list still emitted normally alongside healthCheck.
        assert load_balancer["servers"] == [{"url": "http://127.0.0.1:8000/"}]

    def test_single_healthcheck_directive_for_multi_route_service(self) -> None:
        # Regression: healthCheck must be attached once at the loadBalancer level,
        # not duplicated per kernel server.
        r1 = _make_route(kernel_port=8000)
        r2 = _make_route(kernel_port=8001)
        circuit = _make_inference_circuit(
            routes=[r1, r2],
            health_check_enabled=True,
            health_check_config=_default_health_check_config(),
        )

        services = circuit.traefik_services
        load_balancer = services[f"bai_service_{circuit.id}"]["loadBalancer"]

        assert "healthCheck" in load_balancer
        assert len(load_balancer["servers"]) == 2

    def test_http_inference_without_health_check_omits_directive(self) -> None:
        route = _make_route()
        circuit = _make_inference_circuit(
            routes=[route],
            health_check_enabled=False,
            health_check_config=None,
        )

        services = circuit.traefik_services

        load_balancer = services[f"bai_service_{circuit.id}"]["loadBalancer"]
        assert "healthCheck" not in load_balancer

    def test_http_inference_with_missing_config_omits_directive(self) -> None:
        # health_check_enabled=True but config is None (edge case)
        route = _make_route()
        circuit = _make_inference_circuit(
            routes=[route],
            health_check_enabled=True,
            health_check_config=None,
        )

        services = circuit.traefik_services

        load_balancer = services[f"bai_service_{circuit.id}"]["loadBalancer"]
        assert "healthCheck" not in load_balancer

    def test_tcp_mode_never_includes_health_check(self) -> None:
        # Traefik TCP services use different healthCheck syntax; we intentionally
        # skip directive injection for TCP circuits in this PR.
        route = _make_route()
        circuit = _make_inference_circuit(
            routes=[route],
            protocol=ProxyProtocol.TCP,
            health_check_enabled=True,
            health_check_config=_default_health_check_config(),
        )

        services = circuit.traefik_services

        load_balancer = services[f"bai_service_{circuit.id}"]["loadBalancer"]
        assert "healthCheck" not in load_balancer
        # TCP servers use `address` field.
        assert load_balancer["servers"] == [{"address": "127.0.0.1:8000"}]

    def test_non_inference_circuit_omits_health_check(self) -> None:
        # Interactive-mode circuits should never get loadBalancer.healthCheck
        # since health_check_config semantics only apply to inference endpoints.
        route = _make_route()
        circuit = _make_inference_circuit(
            routes=[route],
            health_check_enabled=True,
            health_check_config=_default_health_check_config(),
            app_mode=AppMode.INTERACTIVE,
        )

        services = circuit.traefik_services

        load_balancer = services[f"bai_service_{circuit.id}"]["loadBalancer"]
        assert "healthCheck" not in load_balancer


class TestCircuitTraefikServicesUnhealthyRoutesExposed:
    """Traefik owns unhealthy-route ejection via its own healthCheck probes."""

    def test_unhealthy_routes_still_appear_in_servers_list(self) -> None:
        # The coordinator no longer pre-filters route_info by health status:
        # every route is fed into Traefik which decides which backend receives traffic.
        healthy = _make_route(kernel_port=8000)
        unhealthy = _make_route(kernel_port=8001)
        unhealthy.health_status = ModelServiceStatus.UNHEALTHY

        circuit = _make_inference_circuit(
            routes=[healthy, unhealthy],
            health_check_enabled=True,
            health_check_config=_default_health_check_config(),
        )

        services = circuit.traefik_services
        servers = services[f"bai_service_{circuit.id}"]["loadBalancer"]["servers"]

        assert {"url": "http://127.0.0.1:8000/"} in servers
        assert {"url": "http://127.0.0.1:8001/"} in servers
