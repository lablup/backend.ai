"""Query specs for the ssh_keypairs table."""

from __future__ import annotations

from dataclasses import dataclass
from typing import Any, override

import sqlalchemy as sa
from sqlalchemy.orm import InstrumentedAttribute

from ai.backend.common.data.entity.user import UserID
from ai.backend.manager.data.ssh_keypair.types import SSHKeypairData
from ai.backend.manager.models.specs.querier import OwnedFieldQuerier
from ai.backend.manager.models.ssh_keypair.row import SSHKeypairRow


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
        return SSHKeypairData(
            id=row.id,
            user_id=row.user_id,
            public_key=row.public_key,
            private_key=row.private_key,
            is_default=row.is_default,
        )
