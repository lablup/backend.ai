import uuid
from dataclasses import dataclass
from typing import Optional, override

from ai.backend.manager.actions.action import BaseActionResult
from ai.backend.manager.data.auth.types import SSHKeypair
from ai.backend.manager.services.auth.actions.base import AuthAction


@dataclass
class UploadSSHKeypairAction(AuthAction):
    user_id: uuid.UUID
    public_key: str
    private_key: str
    access_key: str

    @override
    def entity_id(self) -> Optional[str]:
        return str(self.user_id)

    @override
    @classmethod
    def operation_type(cls) -> str:
        return "upload_ssh_keypair"


@dataclass
class UploadSSHKeypairActionResult(BaseActionResult):
    ssh_keypair: SSHKeypair

    @override
    def entity_id(self) -> Optional[str]:
        return None
