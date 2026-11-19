from __future__ import annotations

from ai.backend.manager.models.keypair.ssh_key_validator import SSHKeyValidator
from ai.backend.manager.repositories.ssh_key.repository import SSHKeyRepository
from ai.backend.manager.services.ssh_key.actions.switch_default import (
    SwitchDefaultSSHKeyAction,
    SwitchDefaultSSHKeyActionResult,
)
from ai.backend.manager.services.ssh_key.actions.upload import (
    UploadSSHKeyAction,
    UploadSSHKeyActionResult,
)


class SSHKeyService:
    _repository: SSHKeyRepository
    _ssh_key_validator: SSHKeyValidator

    def __init__(self, repository: SSHKeyRepository, ssh_key_validator: SSHKeyValidator) -> None:
        self._repository = repository
        self._ssh_key_validator = ssh_key_validator

    async def upload(self, action: UploadSSHKeyAction) -> UploadSSHKeyActionResult:
        self._ssh_key_validator.validate(action.public_key)
        ssh_key = await self._repository.upload(action.user_id, action.public_key)
        return UploadSSHKeyActionResult(ssh_key=ssh_key)

    async def switch_default(
        self, action: SwitchDefaultSSHKeyAction
    ) -> SwitchDefaultSSHKeyActionResult:
        ssh_key = await self._repository.switch_default(action.ssh_key_id)
        return SwitchDefaultSSHKeyActionResult(ssh_key=ssh_key)
