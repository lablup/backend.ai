from __future__ import annotations

from collections.abc import Sequence
from dataclasses import dataclass, replace
from typing import Self, override

from ai.backend.common.data.entity.ssh_keypair import SSHKeypairID
from ai.backend.common.data.entity.user import UserID
from ai.backend.manager.actions.v2.field.ops import PartialBulkGetFieldOpsAction
from ai.backend.manager.data.ssh_keypair.types import SSHKeypairData
from ai.backend.manager.models.ssh_keypair.queriers import BulkSSHKeyQuerier
from ai.backend.manager.models.ssh_keypair.row import SSHKeypairRow
from ai.backend.manager.services.ssh_key.actions.lookup_owner import (
    LookupBulkSSHKeypairOwnerAction,
)


@dataclass(frozen=True)
class BulkGetSSHKeysAction(
    PartialBulkGetFieldOpsAction[SSHKeypairID, UserID, SSHKeypairRow, SSHKeypairData]
):
    """Read the SSH keys the caller named, checked per owning user."""

    ids: Sequence[SSHKeypairID]

    @override
    @classmethod
    def action_name(cls) -> str:
        return "bulk_get_ssh_keys"

    @override
    def field_ids(self) -> Sequence[SSHKeypairID]:
        return tuple(self.ids)

    @override
    def to_owner_lookup_action(self) -> LookupBulkSSHKeypairOwnerAction:
        return LookupBulkSSHKeypairOwnerAction(ssh_keypair_ids=self.ids)

    @override
    def to_querier(self) -> BulkSSHKeyQuerier:
        return BulkSSHKeyQuerier()

    @override
    def narrowed_to(self, field_ids: Sequence[SSHKeypairID]) -> Self:
        allowed = frozenset(field_ids)
        return replace(self, ids=[field_id for field_id in self.ids if field_id in allowed])
