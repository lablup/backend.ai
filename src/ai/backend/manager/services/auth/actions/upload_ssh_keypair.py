from dataclasses import dataclass
from typing import override

from ai.backend.manager.actions.types import ActionOperationType
from ai.backend.manager.data.auth.types import SSHKeypair
from ai.backend.manager.services.auth.actions.base import UserEntityAction


@dataclass(frozen=True)
class UploadSSHKeypairAction(UserEntityAction):
    """Overwrite the SSH keypair the named user's keypair carries with a given one."""

    public_key: str
    private_key: str
    access_key: str

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
    ssh_keypair: SSHKeypair
