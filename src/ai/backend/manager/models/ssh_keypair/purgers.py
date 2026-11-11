"""Purge specs for the ssh_keypairs table."""

from __future__ import annotations

from collections.abc import Sequence
from typing import Any, override

import sqlalchemy as sa

from ai.backend.common.data.entity.user import UserID
from ai.backend.manager.data.ssh_keypair.types import SSHKeypairData
from ai.backend.manager.models.specs.purger import FieldBatchPurger
from ai.backend.manager.models.specs.types import ConflictCheck
from ai.backend.manager.models.ssh_keypair.row import SSHKeypairRow
from ai.backend.manager.models.ssh_keypair.searchable_fields import SSHKeypairSearchableFields

__all__ = ("DefaultSSHKeypairPurger",)


class DefaultSSHKeypairPurger(FieldBatchPurger[UserID, SSHKeypairRow, SSHKeypairData]):
    """Removes the SSH keypair the user marked default."""

    @override
    def build_subquery(self, owner_id: UserID) -> sa.sql.Select[Any]:
        return sa.select(SSHKeypairRow).where(
            SSHKeypairRow.user_id == owner_id, SSHKeypairRow.is_default
        )

    @override
    def conflict_checks(self) -> Sequence[ConflictCheck]:
        return ()

    @override
    def to_data(self, row: SSHKeypairRow) -> SSHKeypairData:
        return SSHKeypairSearchableFields.own.to_data(row)
