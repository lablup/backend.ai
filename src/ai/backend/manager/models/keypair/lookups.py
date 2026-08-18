"""Lookup implementations for the keypair table, which is a field of its user."""

from __future__ import annotations

from collections.abc import Sequence
from dataclasses import dataclass
from typing import override

from ai.backend.common.types import AccessKey
from ai.backend.manager.data.keypair.types import KeyPairData
from ai.backend.manager.models.clauses import QueryCondition
from ai.backend.manager.models.keypair.row import KeyPairRow
from ai.backend.manager.models.specs.lookup import DataLookup


@dataclass
class KeypairAccessKeyLookup(DataLookup[KeyPairRow, KeyPairData]):
    """Resolves an access key into the keypair it names.

    The access key is the table's primary key, but it is the caller-facing name rather
    than an id, so reaching a keypair by it is a lookup like any other name.
    """

    access_key: AccessKey

    @override
    def row_class(self) -> type[KeyPairRow]:
        return KeyPairRow

    @override
    def conditions(self) -> Sequence[QueryCondition]:
        return [lambda: KeyPairRow.access_key == self.access_key]

    @override
    def to_data(self, row: KeyPairRow) -> KeyPairData:
        return row.to_data()
