from dataclasses import dataclass
from typing import override

from ai.backend.common.types import AccessKey, SSHPublicKey
from ai.backend.manager.actions.types import ActionOperationType
from ai.backend.manager.services.auth.actions.base import UserEntityAction


@dataclass(frozen=True)
class UploadSSHKeypairAction(UserEntityAction):
    """Overwrite the SSH public key the named user's keypair carries with a given one."""

    public_key: SSHPublicKey
    access_key: AccessKey

    @override
    @classmethod
    def operation_type(cls) -> ActionOperationType:
        return ActionOperationType.UPDATE

    @override
    @classmethod
    def action_name(cls) -> str:
        return "upload_ssh_keypair"


@dataclass(frozen=True)
class UploadSSHKeypairActionResult:
    public_key: SSHPublicKey
