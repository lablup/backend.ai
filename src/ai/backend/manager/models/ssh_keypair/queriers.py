"""Query specs for the ssh_keypairs table."""

from __future__ import annotations

from dataclasses import dataclass
from typing import Any, override

import sqlalchemy as sa
from sqlalchemy.orm import InstrumentedAttribute

from ai.backend.common.data.entity.ssh_keypair import SSHKeypairID
from ai.backend.common.data.entity.user import UserID
from ai.backend.manager.data.ssh_keypair.types import SSHKeypairData
from ai.backend.manager.models.specs.querier import (
    BulkFieldQuerier,
    FieldQuerier,
    OwnedFieldQuerier,
)
from ai.backend.manager.models.ssh_keypair.row import SSHKeypairRow
from ai.backend.manager.models.ssh_keypair.searchable_fields import SSHKeypairSearchableFields

__all__ = (
    "BulkSSHKeyQuerier",
    "DefaultSSHKeypairQuerier",
    "SSHKeyQuerier",
)


@dataclass
class DefaultSSHKeypairQuerier(OwnedFieldQuerier[UserID, SSHKeypairRow, SSHKeypairData]):
    """The SSH keypair a user marked default. ``uq_ssh_keypairs_is_default`` caps the
    mark at one per user."""

    @override
    def build_select(self) -> sa.sql.Select[Any]:
        return sa.select(SSHKeypairRow).where(SSHKeypairRow.is_default)

    @override
    def owner_id_column(self) -> InstrumentedAttribute[Any]:
        return SSHKeypairRow.user_id

    @override
    def to_data(self, row: SSHKeypairRow) -> SSHKeypairData:
        return SSHKeypairSearchableFields.own.to_data(row)


@dataclass
class SSHKeyQuerier(FieldQuerier[SSHKeypairRow, SSHKeypairData]):
    """One SSH keypair by its id."""

    ssh_key_id: SSHKeypairID

    @override
    def row_class(self) -> type[SSHKeypairRow]:
        return SSHKeypairRow

    @override
    def target_id_column(self) -> InstrumentedAttribute[Any]:
        return SSHKeypairRow.id

    @override
    def target_id_value(self) -> SSHKeypairID:
        return self.ssh_key_id

    @override
    def to_data(self, row: SSHKeypairRow) -> SSHKeypairData:
        return SSHKeypairSearchableFields.own.to_data(row)


class BulkSSHKeyQuerier(BulkFieldQuerier[SSHKeypairRow, SSHKeypairData]):
    """The SSH keys the caller named."""

    @override
    def row_class(self) -> type[SSHKeypairRow]:
        return SSHKeypairRow

    @override
    def target_id_column(self) -> InstrumentedAttribute[Any]:
        return SSHKeypairRow.id

    @override
    def to_data(self, row: SSHKeypairRow) -> SSHKeypairData:
        return SSHKeypairSearchableFields.own.to_data(row)
