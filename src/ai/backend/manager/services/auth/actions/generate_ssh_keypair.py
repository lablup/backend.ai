from dataclasses import dataclass
from typing import override

from ai.backend.manager.actions.types import ActionOperationType
from ai.backend.manager.data.auth.types import SSHKeypair
from ai.backend.manager.services.auth.actions.base import UserEntityAction


@dataclass(frozen=True)
class GenerateSSHKeypairAction(UserEntityAction):
    """Replace the SSH keypair the named user's keypair carries with a fresh one."""

    access_key: str

    @override
    @classmethod
    def operation_type(cls) -> ActionOperationType:
        return ActionOperationType.UPDATE

    @override
    @classmethod
    def action_name(cls) -> str:
        return "generate_ssh_keypair"


@dataclass(frozen=True)
class GenerateSSHKeypairActionResult:
    ssh_keypair: SSHKeypair
