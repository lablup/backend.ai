from __future__ import annotations

import ipaddress
from dataclasses import dataclass, field
from unittest.mock import Mock

import pytest

from ai.backend.appproxy.common.config import PermitHashConfig, SecretConfig
from ai.backend.appproxy.coordinator.clients.worker.traefik_routing_config import (
    IpAllowListMiddlewareConfig,
    TcpRouterConfig,
    TraefikRoutingConfigFactory,
    TraefikRoutingConfigFactoryArgs,
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
    expected_ip_allowlist_middleware_config: IpAllowListMiddlewareConfig


@dataclass(frozen=True)
class _ClientIPRuleCase:
    name: str
    ranges: list[str] = field(default_factory=list)
    expected_rule: str = ""


@pytest.fixture
def routing_config_factory(case: _ClientIPStrategyCase) -> TraefikRoutingConfigFactory:
    return TraefikRoutingConfigFactory(
        TraefikRoutingConfigFactoryArgs(
            traefik_config=Mock(spec=TraefikConfig, client_ip_strategy=case.strategy),
            secrets=Mock(spec=SecretConfig, jwt_secret="jwt-secret"),
            permit_hash=Mock(spec=PermitHashConfig, secret=b"permit-hash-secret"),
        )
    )


@pytest.fixture
def routing_config_factory_without_client_ip_strategy() -> TraefikRoutingConfigFactory:
    return TraefikRoutingConfigFactory(
        TraefikRoutingConfigFactoryArgs(
            traefik_config=Mock(spec=TraefikConfig, client_ip_strategy=None),
            secrets=Mock(spec=SecretConfig, jwt_secret="jwt-secret"),
            permit_hash=Mock(spec=PermitHashConfig, secret=b"permit-hash-secret"),
        )
    )


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
            _ClientIPStrategyCase(
                name="no-strategy",
                strategy=None,
                expected_ip_allowlist_middleware_config={
                    "ipAllowList": {"sourceRange": ["192.168.0.0/24"]},
                },
            ),
            _ClientIPStrategyCase(
                name="depth",
                strategy=ClientIPStrategyConfig(depth=2, excluded_ips=[]),
                expected_ip_allowlist_middleware_config={
                    "ipAllowList": {
                        "sourceRange": ["192.168.0.0/24"],
                        "ipStrategy": {"depth": 2},
                    },
                },
            ),
            _ClientIPStrategyCase(
                name="excluded-ips",
                strategy=ClientIPStrategyConfig(
                    depth=None, excluded_ips=[ipaddress.ip_network("10.0.0.0/8")]
                ),
                expected_ip_allowlist_middleware_config={
                    "ipAllowList": {
                        "sourceRange": ["192.168.0.0/24"],
                        "ipStrategy": {"excludedIPs": ["10.0.0.0/8"]},
                    },
                },
            ),
        ],
        ids=lambda case: case.name,
    )
    def test_ip_allowlist_reads_the_client_ip_strategy(
        self,
        case: _ClientIPStrategyCase,
        routing_config_factory: TraefikRoutingConfigFactory,
        http_ingress_allowing_one_network: Ingress,
    ) -> None:
        routing_configs = routing_config_factory.routing_configs_by_etcd_key(
            http_ingress_allowing_one_network,
            hostname="worker-1.example.com",
            wildcard_domain=None,
            tls_listen=False,
        )
        assert (
            routing_configs["worker_worker-1/http/middlewares/bai_ingress_10205_ipallowlist"]
            == case.expected_ip_allowlist_middleware_config
        )

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
    ) -> None:
        routing_configs = (
            routing_config_factory_without_client_ip_strategy.routing_configs_by_etcd_key(
                tcp_ingress, hostname="worker-1.example.com", wildcard_domain=None, tls_listen=False
            )
        )
        assert routing_configs[
            "worker_worker-1/tcp/routers/bai_ingress_10205_router"
        ] == TcpRouterConfig(
            rule=case.expected_rule,
            service="bai_ingress_10205_service",
            entrypoints=["portproxy_10205"],
        )
