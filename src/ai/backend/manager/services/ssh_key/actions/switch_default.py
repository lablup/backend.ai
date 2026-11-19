from __future__ import annotations

from dataclasses import dataclass
from typing import override

from ai.backend.common.data.entity.ssh_keypair import SSHKeypairID
from ai.backend.common.data.entity.user import UserID
from ai.backend.manager.actions.types import ActionOperationType
from ai.backend.manager.actions.v2.field.base import BaseSingleFieldAction
from ai.backend.manager.data.ssh_keypair.types import SSHKeypairData
from ai.backend.manager.services.ssh_keypair.actions.lookup_owner import (
    LookupSSHKeypairOwnerAction,
)


@dataclass(frozen=True)
class SwitchDefaultSSHKeypairAction(BaseSingleFieldAction[SSHKeypairID, UserID]):
    """Make one live SSH keypair its user's default."""

    ssh_keypair_id: SSHKeypairID

    @override
    @classmethod
    def operation_type(cls) -> ActionOperationType:
        return ActionOperationType.UPDATE

    @override
    @classmethod
    def action_name(cls) -> str:
        return "switch_default_ssh_keypair"

    @override
    def to_owner_lookup_action(self) -> LookupSSHKeypairOwnerAction:
        return LookupSSHKeypairOwnerAction(ssh_keypair_id=self.ssh_keypair_id)


@dataclass(frozen=True)
class SwitchDefaultSSHKeypairActionResult:
    ssh_keypair: SSHKeypairData
