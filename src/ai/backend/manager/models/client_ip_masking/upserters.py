from __future__ import annotations

from collections.abc import Sequence
from dataclasses import dataclass
from typing import Any, override

import sqlalchemy as sa

from ai.backend.common.data.entity.types import EntityIdentifier
from ai.backend.manager.data.client_ip.masking import ClientIPMaskingMode, ClientIPMaskingTarget
from ai.backend.manager.data.client_ip.types import ClientIPMaskingPolicyData
from ai.backend.manager.models.client_ip_masking.row import ClientIPMaskingPolicyRow
from ai.backend.manager.models.specs.types import IntegrityErrorCheck
from ai.backend.manager.models.specs.upserter import GlobalEntityUpserter

__all__ = ("ClientIPMaskingPolicyUpserter",)


@dataclass
class ClientIPMaskingPolicyUpserter(
    GlobalEntityUpserter[ClientIPMaskingPolicyRow, ClientIPMaskingPolicyData]
):
    """Set the masking one target gets, replacing the row it already has.

    Conflicts are detected on ``target_type``: a target holds one policy, so naming it
    is what identifies the row rather than an id the caller has to look up first.
    """

    target_type: ClientIPMaskingTarget
    mode: ClientIPMaskingMode
    ipv4_prefix: int | None
    ipv6_prefix: int | None

    @override
    def entity_id(self, row: ClientIPMaskingPolicyRow) -> EntityIdentifier:
        return row.id

    @override
    def row_class(self) -> type[ClientIPMaskingPolicyRow]:
        return ClientIPMaskingPolicyRow

    @override
    def index_elements(self) -> list[str]:
        return ["target_type"]

    @override
    def integrity_error_checks(self) -> Sequence[IntegrityErrorCheck]:
        return ()

    @override
    def build_insert_values(self) -> dict[str, Any]:
        return {
            "target_type": self.target_type,
            "mode": self.mode,
            "ipv4_prefix": self.ipv4_prefix,
            "ipv6_prefix": self.ipv6_prefix,
        }

    @override
    def build_update_values(self) -> dict[str, Any]:
        return {
            "mode": self.mode,
            "ipv4_prefix": self.ipv4_prefix,
            "ipv6_prefix": self.ipv6_prefix,
            "updated_at": sa.func.now(),
        }

    @override
    def to_data(self, row: ClientIPMaskingPolicyRow) -> ClientIPMaskingPolicyData:
        return row.to_data()
