from dataclasses import dataclass
from typing import override

from ai.backend.manager.actions.types import ActionOperationType
from ai.backend.manager.services.auth.actions.base import UserEntityAction


@dataclass(frozen=True)
class GetSSHKeypairAction(UserEntityAction):
    """Read the SSH public key the named user's keypair carries."""

    access_key: str

    @override
    @classmethod
    def operation_type(cls) -> ActionOperationType:
        return ActionOperationType.GET

    @override
    @classmethod
    def action_name(cls) -> str:
        return "get_ssh_keypair"


@dataclass(frozen=True)
class GetSSHKeypairActionResult:
    public_key: str
    access_key: str
