"""DataQuerier implementations for the keypair resource policy repository."""

from __future__ import annotations

from dataclasses import dataclass
from typing import override

from ai.backend.manager.data.resource.types import KeyPairResourcePolicyData
from ai.backend.manager.models.resource_policy.row import KeyPairResourcePolicyRow
from ai.backend.manager.models.specs.querier import DataQuerier


@dataclass
class KeyPairResourcePolicyQuerier(
    DataQuerier[KeyPairResourcePolicyRow, KeyPairResourcePolicyData]
):
    name: str

    @override
    def row_class(self) -> type[KeyPairResourcePolicyRow]:
        return KeyPairResourcePolicyRow

    @override
    def pk_value(self) -> str:
        return self.name

    @override
    def to_data(self, row: KeyPairResourcePolicyRow) -> KeyPairResourcePolicyData:
        return row.to_dataclass()
