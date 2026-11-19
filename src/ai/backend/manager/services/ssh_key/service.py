from __future__ import annotations

from ai.backend.manager.models.keypair.ssh_key_validator import SSHKeyValidator
from ai.backend.manager.repositories.ssh_keypair.repository import SSHKeypairRepository
from ai.backend.manager.services.ssh_keypair.actions.switch_default import (
    SwitchDefaultSSHKeypairAction,
    SwitchDefaultSSHKeypairActionResult,
)
from ai.backend.manager.services.ssh_keypair.actions.upload import (
    UploadSSHKeypairAction,
    UploadSSHKeypairActionResult,
)


class SSHKeypairService:
    _repository: SSHKeypairRepository
    _ssh_key_validator: SSHKeyValidator

    def __init__(
        self, repository: SSHKeypairRepository, ssh_key_validator: SSHKeyValidator
    ) -> None:
        self._repository = repository
        self._ssh_key_validator = ssh_key_validator

    async def upload(self, action: UploadSSHKeypairAction) -> UploadSSHKeypairActionResult:
        self._ssh_key_validator.validate(action.public_key)
        ssh_keypair = await self._repository.upload(action.user_id, action.public_key)
        return UploadSSHKeypairActionResult(ssh_keypair=ssh_keypair)

    async def switch_default(
        self, action: SwitchDefaultSSHKeypairAction
    ) -> SwitchDefaultSSHKeypairActionResult:
        ssh_keypair = await self._repository.switch_default(action.ssh_keypair_id)
        return SwitchDefaultSSHKeypairActionResult(ssh_keypair=ssh_keypair)
