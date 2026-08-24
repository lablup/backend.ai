"""Lookup implementations for the keypair table, which is a field of its user."""

from __future__ import annotations

from collections.abc import Sequence
from dataclasses import dataclass
from typing import Any, override
from uuid import UUID

import sqlalchemy as sa

from ai.backend.common.data.entity.keypair import KeyPairID
from ai.backend.common.data.entity.types import EntityType
from ai.backend.common.data.entity.user import USER_ENTITY_TYPE, UserID
from ai.backend.common.types import AccessKey
from ai.backend.manager.models.clauses import QueryCondition
from ai.backend.manager.models.keypair.row import KeyPairRow
from ai.backend.manager.models.specs.lookup import (
    DataLookup,
    FieldKeyLookup,
    FieldOwnerKeyLookup,
    FieldOwnerLookup,
)


@dataclass
class KeypairOwnerLookup(FieldOwnerLookup[KeyPairID, UserID]):
    """Reads the user that owns each of the keypairs named."""

    @override
    def build_query(self, field_ids: Sequence[KeyPairID]) -> sa.sql.Select[Any]:
        return sa.select(KeyPairRow.id, KeyPairRow.user, sa.literal(USER_ENTITY_TYPE)).where(
            KeyPairRow.id.in_(field_ids)
        )

    @override
    def to_entity_id(self, value: UUID, owner_type: EntityType) -> UserID:
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


@dataclass
class KeypairAccessKeyLookup(FieldKeyLookup[KeyPairID, UserID]):
    """Reads the keypair an access key names, and the user that owns it."""

    access_key: AccessKey

    @override
    def build_query(self) -> sa.sql.Select[Any]:
        return sa.select(KeyPairRow.id, KeyPairRow.user).where(
            KeyPairRow.access_key == self.access_key
        )

    @override
    def to_field_id(self, value: UUID) -> KeyPairID:
        return KeyPairID(value)

    @override
    def to_entity_id(self, value: UUID) -> UserID:
        return UserID(value)


@dataclass
class KeypairAccessKeyUserLookup(DataLookup[KeyPairRow, UserID]):
    """Resolves an access key into the user it authenticates as."""

    access_key: AccessKey

    @override
    def row_class(self) -> type[KeyPairRow]:
        return KeyPairRow

    @override
    def conditions(self) -> Sequence[QueryCondition]:
        return [lambda: KeyPairRow.access_key == self.access_key]

    @override
    def to_entity_id(self, row: KeyPairRow) -> UserID:
        return UserID(row.user)
