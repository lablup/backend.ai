"""SSH keypair processor calls and DTO conversion, shared by GQL and REST v2."""

from __future__ import annotations

from ai.backend.common.contexts.user import current_user
from ai.backend.common.data.entity.ssh_keypair import SSHKeypairID
from ai.backend.common.data.entity.user import UserID
from ai.backend.common.dto.manager.v2.ssh_keypair.request import UploadMySSHKeypairInput
from ai.backend.common.dto.manager.v2.ssh_keypair.response import (
    SSHKeypairNode,
    SwitchDefaultSSHKeypairPayload,
    UploadMySSHKeypairPayload,
)
from ai.backend.common.exception import UnreachableError
from ai.backend.common.types import SSHPublicKey
from ai.backend.manager.api.adapters.base import BaseAdapter
from ai.backend.manager.data.ssh_keypair.types import SSHKeypairData
from ai.backend.manager.services.ssh_keypair.actions.switch_default import (
    SwitchDefaultSSHKeypairAction,
)
from ai.backend.manager.services.ssh_keypair.actions.upload import UploadSSHKeypairAction
from ai.backend.manager.services.ssh_keypair.processors import SSHKeypairProcessors


class SSHKeypairAdapter(BaseAdapter):
    _ssh_keypair: SSHKeypairProcessors

    def __init__(self, ssh_keypair: SSHKeypairProcessors) -> None:
        self._ssh_keypair = ssh_keypair

    async def upload_my(self, input: UploadMySSHKeypairInput) -> UploadMySSHKeypairPayload:
        """Upload a public key to the current user."""
        me = current_user()
        if me is None:
            raise UnreachableError("User context is not available")
        result = await self._ssh_keypair.upload.run(
            UploadSSHKeypairAction(
                user_id=UserID(me.user_id), public_key=SSHPublicKey(input.public_key)
            )
        )
        return UploadMySSHKeypairPayload(ssh_keypair=self._to_node(result.ssh_keypair))

    async def switch_default(self, ssh_keypair_id: SSHKeypairID) -> SwitchDefaultSSHKeypairPayload:
        result = await self._ssh_keypair.switch_default.run(
            SwitchDefaultSSHKeypairAction(ssh_keypair_id=ssh_keypair_id)
        )
        return SwitchDefaultSSHKeypairPayload(ssh_keypair=self._to_node(result.ssh_keypair))

    @staticmethod
    def _to_node(data: SSHKeypairData) -> SSHKeypairNode:
        return SSHKeypairNode(
            id=data.id,
            field_id=data.id,
            user_id=data.user_id,
            public_key=data.public_key,
            is_default=data.is_default,
        )
