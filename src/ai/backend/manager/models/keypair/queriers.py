"""Query specs for the keypairs table."""

from __future__ import annotations

from dataclasses import dataclass
from typing import Any, override

import sqlalchemy as sa
from sqlalchemy.orm import InstrumentedAttribute

from ai.backend.common.data.entity.user import UserID
from ai.backend.manager.data.keypair.types import KeyPairData
from ai.backend.manager.models.keypair.row import KeyPairRow
from ai.backend.manager.models.specs.querier import OwnedFieldQuerier

__all__ = ("DefaultKeypairQuerier",)


@dataclass
class DefaultKeypairQuerier(OwnedFieldQuerier[UserID, KeyPairRow, KeyPairData]):
    """The keypair a user authorizes with: the active one they marked default.

    ``uq_keypairs_is_default`` caps the mark at one per user, so the pair of
    conditions names a single row.
    """

    @override
    def build_select(self) -> sa.sql.Select[Any]:
        return sa.select(KeyPairRow).where(KeyPairRow.is_default & KeyPairRow.is_active)

    @override
    def owner_id_column(self) -> InstrumentedAttribute[Any]:
        return KeyPairRow.user

    @override
    def to_data(self, row: KeyPairRow) -> KeyPairData:
        return row.to_data()
