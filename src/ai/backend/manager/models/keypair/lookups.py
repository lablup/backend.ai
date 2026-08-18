"""Lookup implementations for the keypair table, which is a field of its user."""

from __future__ import annotations

from collections.abc import Sequence
from dataclasses import dataclass
from typing import Any, override
from uuid import UUID

import sqlalchemy as sa

from ai.backend.common.data.entity.keypair import KeyPairID
from ai.backend.common.data.entity.user import UserID
from ai.backend.common.types import AccessKey
from ai.backend.manager.data.keypair.types import KeyPairData
from ai.backend.manager.models.clauses import QueryCondition
from ai.backend.manager.models.keypair.row import KeyPairRow
from ai.backend.manager.models.specs.lookup import (
    DataLookup,
    FieldOwnerKeyLookup,
    FieldOwnerLookup,
)


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


@dataclass
class KeypairOwnerLookup(FieldOwnerLookup[KeyPairID, UserID]):
    """Reads the user that owns each of the keypairs named."""

    @override
    def build_query(self, field_ids: Sequence[KeyPairID]) -> sa.sql.Select[Any]:
        return sa.select(KeyPairRow.id, KeyPairRow.user).where(KeyPairRow.id.in_(field_ids))

    @override
    def to_entity_id(self, value: UUID) -> UserID:
        return UserID(value)


@dataclass
class KeypairAccessKeyOwnerLookup(FieldOwnerKeyLookup[UserID]):
    """Reads the user that owns the keypair an access key names."""

    access_key: AccessKey

    @override
    def build_query(self) -> sa.sql.Select[Any]:
        return sa.select(KeyPairRow.user).where(KeyPairRow.access_key == self.access_key)

    @override
    def to_entity_id(self, value: UUID) -> UserID:
        return UserID(value)
