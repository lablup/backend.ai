from __future__ import annotations

import json
from dataclasses import dataclass, field
from typing import Any, override

from aiohttp import web
from aiohttp.test_utils import make_mocked_request

from ai.backend.manager.server import build_prometheus_service_discovery_handler


@dataclass
class _Endpoint:
    prometheus_address: str

    @override
    def __str__(self) -> str:
        return self.prometheus_address


@dataclass
class _Service:
    id: str
    endpoint: _Endpoint
    service_group: str
    display_name: str
    version: str = "26.9.0a4"
    labels: dict[str, str] = field(default_factory=dict)


class _StubDiscovery:
    def __init__(self, services: list[_Service]) -> None:
        self._services = services

    async def discover(self) -> list[_Service]:
        return self._services


def _manager_workers(address: str, count: int) -> list[_Service]:
    """The registrations a manager with ``num-proc`` = *count* leaves behind.

    Every worker registers itself, and they all share one listening socket, so the
    address repeats.
    """
    return [
        _Service(
            id=f"worker-{i}",
            endpoint=_Endpoint(address),
            service_group="manager",
            display_name="manager-i-core1",
        )
        for i in range(count)
    ]


async def _targets(services: list[_Service]) -> list[dict[str, Any]]:
    handler = build_prometheus_service_discovery_handler(_StubDiscovery(services))
    response = await handler(make_mocked_request("GET", "/metrics/service_discovery"))
    assert isinstance(response, web.Response)
    assert response.text is not None
    targets: list[dict[str, Any]] = json.loads(response.text)
    return targets


async def test_workers_sharing_an_address_are_scraped_once() -> None:
    """Metrics are collected per host, so a repeated address must not repeat the target.

    Prometheus scraping one address once per worker reads the same host-wide totals that
    many times, and every ``sum()`` over them comes out inflated by ``num-proc``.
    """
    targets = await _targets(_manager_workers("10.0.0.1:18080", 4))

    assert len(targets) == 1
    assert targets[0]["targets"] == ["10.0.0.1:18080"]


async def test_distinct_addresses_are_all_kept() -> None:
    services = [
        *_manager_workers("10.0.0.1:18080", 4),
        *_manager_workers("10.0.0.2:18080", 4),
        _Service(
            id="agent-1",
            endpoint=_Endpoint("10.0.0.3:6003"),
            service_group="agent",
            display_name="agent-cpu1",
        ),
    ]

    targets = await _targets(services)

    assert [t["targets"][0] for t in targets] == [
        "10.0.0.1:18080",
        "10.0.0.2:18080",
        "10.0.0.3:6003",
    ]


async def test_the_surviving_target_carries_no_worker_identity() -> None:
    """No single worker's id speaks for the host, so it goes with the duplicates."""
    targets = await _targets(_manager_workers("10.0.0.1:18080", 4))

    labels = targets[0]["labels"]
    assert "service_id" not in labels
    assert labels["service_group"] == "manager"
    assert labels["display_name"] == "manager-i-core1"
    assert labels["version"] == "26.9.0a4"
