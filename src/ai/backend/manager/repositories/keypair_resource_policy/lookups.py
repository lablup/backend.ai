"""DataLookup implementations for the keypair resource policy repository."""

from __future__ import annotations

from collections.abc import Sequence
from dataclasses import dataclass
from typing import override

from ai.backend.manager.data.resource.types import KeyPairResourcePolicyData
from ai.backend.manager.models.clauses import QueryCondition
from ai.backend.manager.models.resource_policy.row import KeyPairResourcePolicyRow
from ai.backend.manager.models.specs.lookup import DataLookup

__all__ = ("KeypairResourcePolicyNameLookup",)


@dataclass
class KeypairResourcePolicyNameLookup(
    DataLookup[KeyPairResourcePolicyRow, KeyPairResourcePolicyData]
):
    """Resolves a policy's name into the policy it names."""

    name: str

    @override
    def row_class(self) -> type[KeyPairResourcePolicyRow]:
        return KeyPairResourcePolicyRow

    @override
    def conditions(self) -> Sequence[QueryCondition]:
        return [lambda: KeyPairResourcePolicyRow.name == self.name]

    @override
    def to_data(self, row: KeyPairResourcePolicyRow) -> KeyPairResourcePolicyData:
        return row.to_dataclass()
