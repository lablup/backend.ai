"""Lookup implementations for the ssh_keypairs table, which is a field of its user."""

from __future__ import annotations

from collections.abc import Sequence
from dataclasses import dataclass
from typing import Any, override
from uuid import UUID

import sqlalchemy as sa

from ai.backend.common.data.entity.ssh_keypair import SSHKeypairID
from ai.backend.common.data.entity.user import UserID
from ai.backend.manager.models.specs.lookup import FieldOwnerLookup
from ai.backend.manager.models.ssh_keypair.row import SSHKeypairRow


@dataclass
class SSHKeypairOwnerLookup(FieldOwnerLookup[SSHKeypairID, UserID]):
    """Reads the user that owns each of the SSH keypairs named."""

    @override
    def build_query(self, field_ids: Sequence[SSHKeypairID]) -> sa.sql.Select[Any]:
        return sa.select(SSHKeypairRow.id, SSHKeypairRow.user_id).where(
            SSHKeypairRow.id.in_(field_ids)
        )

    @override
    def to_entity_id(self, value: UUID) -> UserID:
        return UserID(value)
