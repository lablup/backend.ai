"""Write specs for a client IP masking policy."""

from __future__ import annotations

from dataclasses import dataclass
from typing import override

from ai.backend.manager.data.client_ip.masking import ClientIPMaskingMode, ClientIPMaskingTarget
from ai.backend.manager.data.client_ip.types import ClientIPMaskingPolicyData
from ai.backend.manager.models.client_ip_masking.upserters import ClientIPMaskingPolicyUpserter
from ai.backend.testutils.scenario_steps import Says
from bai_scenario.seeds.seeder import Naming, TestSeedRow, joined


@dataclass(frozen=True)
class TestSeedClientIPMaskingPolicy(TestSeedRow[ClientIPMaskingPolicyData]):
    """The one policy of a target. Its name is the target, which the manager fixes."""

    target_type: ClientIPMaskingTarget = ClientIPMaskingTarget.DEFAULT
    mode: ClientIPMaskingMode = ClientIPMaskingMode.TRUNCATE
    ipv4_prefix: int | None = 24
    ipv6_prefix: int | None = 48

    @override
    def kind(self) -> str:
        return Says("클라이언트 IP 마스킹 정책", english="client IP masking policy")

    @override
    def detail(self) -> str:
        parts = [Says(f"{self.mode.value} 모드", english=f"{self.mode.value} mode")]
        if self.ipv4_prefix is not None or self.ipv6_prefix is not None:
            parts.append(
                Says(
                    f"접두 길이 v4 {self.ipv4_prefix}, v6 {self.ipv6_prefix}",
                    english=f"prefix length v4 {self.ipv4_prefix}, v6 {self.ipv6_prefix}",
                )
            )
        return joined(parts)

    @override
    def name(self, naming: Naming) -> str:
        return self.target_type.value

    @override
    def seed(self, name: str) -> ClientIPMaskingPolicyUpserter:
        return ClientIPMaskingPolicyUpserter(
            target_type=self.target_type,
            mode=self.mode,
            ipv4_prefix=self.ipv4_prefix,
            ipv6_prefix=self.ipv6_prefix,
        )
