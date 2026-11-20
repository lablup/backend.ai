from __future__ import annotations

from dataclasses import dataclass
from typing import override

from ai.backend.common.data.entity.types import EntityIdentifier
from ai.backend.common.data.entity.user import UserID
from ai.backend.common.types import SSHPublicKey
from ai.backend.manager.actions.types import ActionOperationType
from ai.backend.manager.actions.v2.single_entity.base import BaseSingleEntityAction
from ai.backend.manager.data.ssh_keypair.types import SSHKeypairData


@dataclass(frozen=True)
class UploadSSHPublicKeyAction(BaseSingleEntityAction):
    """Upload a public key to a user. It becomes the default only when the user has none."""

    user_id: UserID
    public_key: SSHPublicKey

    @override
    def entity_id(self) -> EntityIdentifier:
        return self.user_id

    @override
    @classmethod
    def operation_type(cls) -> ActionOperationType:
        return ActionOperationType.UPDATE

    @override
    @classmethod
    def action_name(cls) -> str:
        return "upload_ssh_public_key"


@dataclass(frozen=True)
class UploadSSHPublicKeyActionResult:
    ssh_key: SSHKeypairData
