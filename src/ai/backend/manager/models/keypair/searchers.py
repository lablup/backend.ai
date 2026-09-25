"""List-read spec for keypairs."""

from __future__ import annotations

from dataclasses import dataclass
from typing import Any, override

import sqlalchemy as sa

from ai.backend.manager.data.keypair.types import KeyPairData
from ai.backend.manager.models.keypair.row import KeyPairRow
from ai.backend.manager.models.keypair.searchable_fields import KeyPairSearchableFields
from ai.backend.manager.models.specs.searcher import Searcher


@dataclass
class KeyPairSearcher(Searcher[KeyPairRow, KeyPairData]):
    """Keypairs matching the conditions."""

    @override
    def build_select(self) -> sa.sql.Select[Any]:
        return sa.select(KeyPairRow)

    @override
    def to_data(self, row: KeyPairRow) -> KeyPairData:
        return KeyPairSearchableFields.own.to_data(row)
