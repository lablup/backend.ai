"""Searcher implementations for the keypair resource policy repository."""

from __future__ import annotations

from dataclasses import dataclass
from typing import Any, override

import sqlalchemy as sa

from ai.backend.manager.data.resource.types import KeyPairResourcePolicyData
from ai.backend.manager.models.resource_policy.row import KeyPairResourcePolicyRow
from ai.backend.manager.models.specs.searcher import Searcher


@dataclass
class KeyPairResourcePolicySearcher(Searcher[KeyPairResourcePolicyRow, KeyPairResourcePolicyData]):
    @override
    def build_select(self) -> sa.sql.Select[Any]:
        return sa.select(KeyPairResourcePolicyRow)

    @override
    def to_data(self, row: KeyPairResourcePolicyRow) -> KeyPairResourcePolicyData:
        return row.to_dataclass()
