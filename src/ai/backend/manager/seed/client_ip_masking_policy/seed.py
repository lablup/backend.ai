from __future__ import annotations

from collections.abc import Sequence
from typing import override

from pydantic import Field

from ai.backend.manager.data.client_ip.masking import (
    MAX_IPV4_PREFIX,
    MAX_IPV6_PREFIX,
    ClientIPMaskingMode,
    ClientIPMaskingTarget,
)
from ai.backend.manager.models.client_ip_masking.upserters import ClientIPMaskingPolicyUpserter
from ai.backend.manager.repositories.ops.v2.seed.types import SeedWrite
from ai.backend.manager.seed.base import SeedItem, SeedItems, SeedRejection


class ClientIPMaskingPolicySeed(SeedItem):
    """One ``client_ip_masking_policies`` row, keyed by its target."""

    target_type: ClientIPMaskingTarget
    mode: ClientIPMaskingMode
    ipv4_prefix: int | None = Field(default=None, ge=0, le=MAX_IPV4_PREFIX)
    ipv6_prefix: int | None = Field(default=None, ge=0, le=MAX_IPV6_PREFIX)

    @override
    def key(self) -> str:
        return self.target_type.value

    @override
    def write(self) -> SeedWrite:
        return SeedWrite(
            upserter=ClientIPMaskingPolicyUpserter(
                target_type=self.target_type,
                mode=self.mode,
                ipv4_prefix=self.ipv4_prefix,
                ipv6_prefix=self.ipv6_prefix,
            ),
            field_upserters=[],
            field_purgers=[],
        )

    @override
    @classmethod
    def reject(cls, files: Sequence[SeedItems[ClientIPMaskingPolicySeed]]) -> list[SeedRejection]:
        return []
