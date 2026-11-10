"""What an SSH keypair search can filter and order by, and how its row becomes data."""

from __future__ import annotations

from typing import override

from ai.backend.manager.data.ssh_keypair.types import SSHKeypairData
from ai.backend.manager.models.specs.conditions.boolean import BoolConditions
from ai.backend.manager.models.specs.conditions.string import StringEqualityConditions
from ai.backend.manager.models.specs.conditions.uuid import UUIDConditions
from ai.backend.manager.models.specs.orders.column import ColumnOrder
from ai.backend.manager.models.specs.search.converter import RowDataConverter
from ai.backend.manager.models.specs.search.field import SearchableField
from ai.backend.manager.models.ssh_keypair.row import SSHKeypairRow


class _SSHKeypairOwnFields(RowDataConverter[SSHKeypairRow, SSHKeypairData]):
    """The SSH keypair's own columns; the private key cannot be filtered or ordered."""

    id = SearchableField(
        SSHKeypairRow.id, UUIDConditions(SSHKeypairRow.id), ColumnOrder(SSHKeypairRow.id)
    )
    user_id = SearchableField(
        SSHKeypairRow.user_id,
        UUIDConditions(SSHKeypairRow.user_id),
        ColumnOrder(SSHKeypairRow.user_id),
    )
    public_key = SearchableField(
        SSHKeypairRow.public_key,
        StringEqualityConditions(SSHKeypairRow.public_key),
        ColumnOrder(SSHKeypairRow.public_key),
    )
    private_key = SearchableField(SSHKeypairRow.private_key, None, None)
    is_default = SearchableField(
        SSHKeypairRow.is_default,
        BoolConditions(SSHKeypairRow.is_default),
        ColumnOrder(SSHKeypairRow.is_default),
    )

    @override
    def to_data(self, row: SSHKeypairRow) -> SSHKeypairData:
        return SSHKeypairData(
            id=self.id.read(row),
            user_id=self.user_id.read(row),
            public_key=self.public_key.read(row),
            private_key=self.private_key.read(row),
            is_default=self.is_default.read(row),
        )


class SSHKeypairSearchableFields:
    own = _SSHKeypairOwnFields()
