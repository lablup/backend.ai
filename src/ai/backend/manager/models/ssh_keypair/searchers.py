"""List-read spec for SSH keypairs."""

from __future__ import annotations

from dataclasses import dataclass
from typing import Any, override

import sqlalchemy as sa

from ai.backend.manager.data.ssh_keypair.types import SSHKeypairData
from ai.backend.manager.models.specs.searcher import Searcher
from ai.backend.manager.models.ssh_keypair.row import SSHKeypairRow
from ai.backend.manager.models.ssh_keypair.searchable_fields import SSHKeypairSearchableFields

__all__ = ("SSHKeypairSearcher",)


@dataclass
class SSHKeypairSearcher(Searcher[SSHKeypairRow, SSHKeypairData]):
    """SSH keypairs matching the conditions."""

    @override
    def build_select(self) -> sa.sql.Select[Any]:
        return sa.select(SSHKeypairRow)

    @override
    def to_data(self, row: SSHKeypairRow) -> SSHKeypairData:
        return SSHKeypairSearchableFields.own.to_data(row)
