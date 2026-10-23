from __future__ import annotations

import ipaddress
from dataclasses import dataclass, field
from typing import Any
from unittest.mock import Mock

import pytest

from ai.backend.appproxy.coordinator.config import ClientIPStrategyConfig, TraefikConfig
from ai.backend.appproxy.coordinator.traefik_routing_config import TraefikRoutingConfigFactory


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
        self, case: _ClientIPStrategyCase, routing_config_factory: TraefikRoutingConfigFactory
    ) -> None:
        ip_allowlist = routing_config_factory.ip_allowlist_middleware_config(["192.168.0.0/24"])[
            "ipAllowList"
        ]
        assert ip_allowlist.get("ipStrategy") == case.expected_ip_strategy
        assert ip_allowlist["sourceRange"] == ["192.168.0.0/24"]

    @pytest.mark.parametrize(
        "case",
        [
            _ClientIPRuleCase(name="open", ranges=[], expected_rule="ClientIP(`0.0.0.0/0`)"),
            _ClientIPRuleCase(
                name="restricted",
                ranges=["192.168.0.0/24", "10.1.2.3/32"],
                expected_rule="ClientIP(`192.168.0.0/24`, `10.1.2.3/32`)",
            ),
        ],
        ids=lambda case: case.name,
    )
    def test_client_ip_rule_matches_the_allowed_ranges(self, case: _ClientIPRuleCase) -> None:
        assert TraefikRoutingConfigFactory.client_ip_rule(case.ranges) == case.expected_rule
