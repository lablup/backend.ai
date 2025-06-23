import uuid
from dataclasses import dataclass
from typing import Optional, override

from ai.backend.manager.actions.action import BaseActionResult
from ai.backend.manager.services.auth.actions.base import AuthAction


@dataclass
class GetSSHKeypairAction(AuthAction):
    user_id: uuid.UUID
    access_key: str

    @override
    def entity_id(self) -> Optional[str]:
        return str(self.user_id)

    @override
    @classmethod
    def operation_type(cls) -> str:
        return "get_ssh_keypair"


@dataclass
class GetSSHKeypairActionResult(BaseActionResult):
    public_key: str

    @override
    def entity_id(self) -> Optional[str]:
        return None
