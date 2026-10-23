from __future__ import annotations

import ipaddress
from dataclasses import dataclass, field
from typing import Any
from unittest.mock import Mock

import pytest

from ai.backend.appproxy.coordinator.clients.worker.traefik_routing_config import (
    TraefikRoutingConfigFactory,
    TraefikWorker,
)
from ai.backend.appproxy.coordinator.config import ClientIPStrategyConfig, TraefikConfig
from ai.backend.common.dto.appproxy.v2.ingress.types import (
    Ingress,
    IngressAccess,
    IngressAccessMode,
    IngressAuthority,
    IngressBackend,
    IngressBackendID,
    IngressFrontend,
    IngressFrontendKind,
    IngressID,
    IngressProtocol,
    IngressTargetGroup,
    IngressTargetGroupID,
    PortFrontend,
)


@dataclass(frozen=True)
class _ClientIPStrategyCase:
    name: str
    strategy: ClientIPStrategyConfig | None
    expected_ip_strategy: dict[str, Any] | None


@dataclass(frozen=True)
class _ClientIPRuleCase:
    name: str
    ranges: list[str] = field(default_factory=list)
    expected_rule: str = ""


@pytest.fixture
def routing_config_factory(case: _ClientIPStrategyCase) -> TraefikRoutingConfigFactory:
    return TraefikRoutingConfigFactory(
        Mock(spec=TraefikConfig, client_ip_strategy=case.strategy),
        jwt_secret="jwt-secret",
        permit_hash_secret="permit-hash-secret",
    )


@pytest.fixture
def routing_config_factory_without_client_ip_strategy() -> TraefikRoutingConfigFactory:
    return TraefikRoutingConfigFactory(
        Mock(spec=TraefikConfig, client_ip_strategy=None),
        jwt_secret="jwt-secret",
        permit_hash_secret="permit-hash-secret",
    )


@pytest.fixture
def worker() -> TraefikWorker:
    return TraefikWorker(hostname="worker-1.example.com", wildcard_domain=None, tls_listen=False)


@pytest.fixture
def http_ingress_allowing_one_network() -> Ingress:
    return Ingress(
        id=IngressID("ingress-10205"),
        authority=IngressAuthority("worker-1"),
        revision=1,
        frontend=IngressFrontend(
            kind=IngressFrontendKind.PORT,
            protocol=IngressProtocol.HTTP,
            port=PortFrontend(number=10205),
        ),
        access=IngressAccess(
            mode=IngressAccessMode.PUBLIC,
            allowed_client_ips=[ipaddress.ip_network("192.168.0.0/24")],
        ),
        backend=IngressBackend(
            id=IngressBackendID("backend-10205"),
            target_groups=[
                IngressTargetGroup(id=IngressTargetGroupID("group-1"), weight=1, targets=[])
            ],
        ),
    )


@pytest.fixture
def tcp_ingress(case: _ClientIPRuleCase) -> Ingress:
    return Ingress(
        id=IngressID("ingress-10205"),
        authority=IngressAuthority("worker-1"),
        revision=1,
        frontend=IngressFrontend(
            kind=IngressFrontendKind.PORT,
            protocol=IngressProtocol.TCP,
            port=PortFrontend(number=10205),
        ),
        access=IngressAccess(
            mode=IngressAccessMode.PUBLIC,
            allowed_client_ips=[ipaddress.ip_network(cidr) for cidr in case.ranges],
        ),
        backend=IngressBackend(
            id=IngressBackendID("backend-10205"),
            target_groups=[
                IngressTargetGroup(id=IngressTargetGroupID("group-1"), weight=1, targets=[])
            ],
        ),
    )


class TestTraefikRoutingConfigFactory:
    @pytest.mark.parametrize(
        "case",
        [
            _ClientIPStrategyCase(name="no-strategy", strategy=None, expected_ip_strategy=None),
            _ClientIPStrategyCase(
                name="depth",
                strategy=ClientIPStrategyConfig(depth=2, excluded_ips=[]),
                expected_ip_strategy={"depth": 2},
            ),
            _ClientIPStrategyCase(
                name="excluded-ips",
                strategy=ClientIPStrategyConfig(
                    depth=None, excluded_ips=[ipaddress.ip_network("10.0.0.0/8")]
                ),
                expected_ip_strategy={"excludedIPs": ["10.0.0.0/8"]},
            ),
        ],
        ids=lambda case: case.name,
    )
    def test_ip_allowlist_reads_the_client_ip_strategy(
        self,
        case: _ClientIPStrategyCase,
        routing_config_factory: TraefikRoutingConfigFactory,
        http_ingress_allowing_one_network: Ingress,
        worker: TraefikWorker,
    ) -> None:
        routing_configs = routing_config_factory.routing_configs_by_etcd_key(
            http_ingress_allowing_one_network, worker
        )
        ip_allowlist = routing_configs[
            "worker_worker-1/http/middlewares/bai_ingress_10205_ipallowlist"
        ]["ipAllowList"]
        assert ip_allowlist.get("ipStrategy") == case.expected_ip_strategy
        assert ip_allowlist["sourceRange"] == ["192.168.0.0/24"]

    @pytest.mark.parametrize(
        "case",
        [
            _ClientIPRuleCase(name="open", ranges=[], expected_rule="ClientIP(`0.0.0.0/0`)"),
            _ClientIPRuleCase(
                name="restricted",
                ranges=["192.168.0.0/24", "10.1.2.3/32"],
                expected_rule="ClientIP(`192.168.0.0/24`) || ClientIP(`10.1.2.3/32`)",
            ),
        ],
        ids=lambda case: case.name,
    )
    def test_tcp_router_rule_matches_the_allowed_client_ips(
        self,
        case: _ClientIPRuleCase,
        routing_config_factory_without_client_ip_strategy: TraefikRoutingConfigFactory,
        tcp_ingress: Ingress,
        worker: TraefikWorker,
    ) -> None:
        routing_configs = (
            routing_config_factory_without_client_ip_strategy.routing_configs_by_etcd_key(
                tcp_ingress, worker
            )
        )
        router_config = routing_configs["worker_worker-1/tcp/routers/bai_ingress_10205_router"]
        assert router_config["rule"] == case.expected_rule
