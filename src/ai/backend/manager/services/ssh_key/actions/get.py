from __future__ import annotations

from dataclasses import dataclass
from typing import override

from ai.backend.common.data.entity.ssh_keypair import SSHKeypairID
from ai.backend.common.data.entity.user import UserID
from ai.backend.manager.actions.v2.field.ops import GetFieldOpsAction
from ai.backend.manager.data.ssh_keypair.types import SSHKeypairData
from ai.backend.manager.models.ssh_keypair.queriers import SSHKeyQuerier
from ai.backend.manager.models.ssh_keypair.row import SSHKeypairRow
from ai.backend.manager.services.ssh_key.actions.lookup_owner import (
    LookupSSHKeypairOwnerAction,
)


@dataclass(frozen=True)
class GetSSHKeyAction(GetFieldOpsAction[SSHKeypairID, UserID, SSHKeypairRow, SSHKeypairData]):
    """Read one SSH key, authorized against the user owning it."""

    ssh_key_id: SSHKeypairID

    @override
    @classmethod
    def action_name(cls) -> str:
        return "get_ssh_key"

    @override
    def to_owner_lookup_action(self) -> LookupSSHKeypairOwnerAction:
        return LookupSSHKeypairOwnerAction(ssh_keypair_id=self.ssh_key_id)

    @override
    def to_querier(self) -> SSHKeyQuerier:
        return SSHKeyQuerier(ssh_key_id=self.ssh_key_id)
