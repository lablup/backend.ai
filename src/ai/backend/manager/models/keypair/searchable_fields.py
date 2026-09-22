"""What a keypair search can filter and order by, and how a keypair row becomes data."""

from __future__ import annotations

from typing import override

from ai.backend.common.types import AccessKey
from ai.backend.manager.data.keypair.types import KeyPairData
from ai.backend.manager.models.keypair.row import KeyPairRow
from ai.backend.manager.models.specs.conditions.boolean import BoolConditions
from ai.backend.manager.models.specs.conditions.datetime import DateTimeConditions
from ai.backend.manager.models.specs.conditions.integer import IntConditions
from ai.backend.manager.models.specs.conditions.string import StringConditions
from ai.backend.manager.models.specs.conditions.uuid import UUIDConditions
from ai.backend.manager.models.specs.orders.column import ColumnOrder
from ai.backend.manager.models.specs.search.converter import RowDataConverter
from ai.backend.manager.models.specs.search.field import SearchableField


class _KeyPairOwnFields(RowDataConverter[KeyPairRow, KeyPairData]):
    """The keypair's own columns.

    ``secret_key`` is a ``SecretColumn``, and ``ssh_private_key`` and
    ``bootstrap_script`` hold values a repeated partial match would recover, so those
    three keep both slots empty. ``dotfiles`` is a binary blob, which no comparison
    orders. ``ssh_public_key`` is ``sa.Text`` with no index serving a partial match, so
    both slots stay empty until a caller needs equality.

    ``access_key`` is open: it is this row's own identifier and the response returns it,
    so no filter recovers anything the caller was not already given. The access key
    copied onto another table (``sessions.access_key``) stays closed.
    """

    field_id = SearchableField(
        KeyPairRow.id, UUIDConditions(KeyPairRow.id), ColumnOrder(KeyPairRow.id)
    )
    user_id = SearchableField(
        KeyPairRow.user, UUIDConditions(KeyPairRow.user), ColumnOrder(KeyPairRow.user)
    )
    access_key = SearchableField(
        KeyPairRow.access_key,
        StringConditions(KeyPairRow.access_key),
        ColumnOrder(KeyPairRow.access_key),
    )
    secret_key = SearchableField(KeyPairRow.secret_key, None, None)
    is_active = SearchableField(
        KeyPairRow.is_active,
        BoolConditions(KeyPairRow.is_active),
        ColumnOrder(KeyPairRow.is_active),
    )
    is_admin = SearchableField(
        KeyPairRow.is_admin, BoolConditions(KeyPairRow.is_admin), ColumnOrder(KeyPairRow.is_admin)
    )
    is_default = SearchableField(
        KeyPairRow.is_default,
        BoolConditions(KeyPairRow.is_default),
        ColumnOrder(KeyPairRow.is_default),
    )
    created_at = SearchableField(
        KeyPairRow.created_at,
        DateTimeConditions(KeyPairRow.created_at),
        ColumnOrder(KeyPairRow.created_at),
    )
    modified_at = SearchableField(
        KeyPairRow.updated_at,
        DateTimeConditions(KeyPairRow.updated_at),
        ColumnOrder(KeyPairRow.updated_at),
    )
    resource_policy_name = SearchableField(
        KeyPairRow.resource_policy,
        StringConditions(KeyPairRow.resource_policy),
        ColumnOrder(KeyPairRow.resource_policy),
    )
    rate_limit = SearchableField(
        KeyPairRow.rate_limit,
        IntConditions(KeyPairRow.rate_limit),
        ColumnOrder(KeyPairRow.rate_limit),
    )
    ssh_public_key = SearchableField(KeyPairRow.ssh_public_key, None, None)
    ssh_private_key = SearchableField(KeyPairRow.ssh_private_key, None, None)
    dotfiles = SearchableField(KeyPairRow.dotfiles, None, None)
    bootstrap_script = SearchableField(KeyPairRow.bootstrap_script, None, None)
    last_used = SearchableField(
        KeyPairRow.last_used,
        DateTimeConditions(KeyPairRow.last_used),
        ColumnOrder(KeyPairRow.last_used),
    )
    num_queries = SearchableField(
        KeyPairRow.num_queries,
        IntConditions(KeyPairRow.num_queries),
        ColumnOrder(KeyPairRow.num_queries),
    )

    @override
    def to_data(self, row: KeyPairRow) -> KeyPairData:
        dotfiles = self.dotfiles.read(row)
        return KeyPairData(
            id=self.field_id.read(row),
            user_id=self.user_id.read(row),
            access_key=AccessKey(self.access_key.read(row)),
            secret_key=self.secret_key.read(row),
            is_active=self.is_active.read(row),
            is_admin=self.is_admin.read(row),
            is_default=self.is_default.read(row),
            created_at=self.created_at.read(row),
            modified_at=self.modified_at.read(row),
            resource_policy_name=self.resource_policy_name.read(row),
            rate_limit=self.rate_limit.read(row),
            ssh_public_key=self.ssh_public_key.read(row),
            ssh_private_key=self.ssh_private_key.read(row),
            dotfiles=dotfiles if dotfiles else b"\x90",
            bootstrap_script=self.bootstrap_script.read(row),
            last_used=self.last_used.read(row),
            num_queries=self.num_queries.read(row),
        )


class KeyPairSearchableFields:
    own = _KeyPairOwnFields()
