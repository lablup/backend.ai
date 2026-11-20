"""SSH key processor calls and DTO conversion, shared by GQL and REST v2."""

from __future__ import annotations

from ai.backend.common.contexts.user import current_user
from ai.backend.common.data.entity.ssh_keypair import SSHKeypairID
from ai.backend.common.data.entity.user import UserID
from ai.backend.common.dto.manager.v2.ssh_key.request import MyUploadSSHKeyInput
from ai.backend.common.dto.manager.v2.ssh_key.response import SSHKeyNode
from ai.backend.common.exception import UnreachableError
from ai.backend.common.types import SSHPublicKey
from ai.backend.manager.api.adapters.base import BaseAdapter
from ai.backend.manager.data.ssh_keypair.types import SSHKeypairData
from ai.backend.manager.services.ssh_key.actions.switch_default import (
    SwitchDefaultSSHKeyAction,
)
from ai.backend.manager.services.ssh_key.actions.upload import UploadSSHPublicKeyAction
from ai.backend.manager.services.ssh_key.processors import SSHKeyProcessors


class SSHKeyAdapter(BaseAdapter):
    _ssh_key: SSHKeyProcessors

    def __init__(self, ssh_key: SSHKeyProcessors) -> None:
        self._ssh_key = ssh_key

    async def my_upload(self, input: MyUploadSSHKeyInput) -> SSHKeyNode:
        """Upload a public key to the current user."""
        me = current_user()
        if me is None:
            raise UnreachableError("User context is not available")
        result = await self._ssh_key.upload.run(
            UploadSSHPublicKeyAction(
                user_id=UserID(me.user_id), public_key=SSHPublicKey(input.public_key)
            )
        )
        return self._to_node(result.ssh_key)

    async def switch_default(self, ssh_key_id: SSHKeypairID) -> SSHKeyNode:
        result = await self._ssh_key.switch_default.run(
            SwitchDefaultSSHKeyAction(ssh_key_id=ssh_key_id)
        )
        return self._to_node(result.ssh_key)

    @staticmethod
    def _to_node(data: SSHKeypairData) -> SSHKeyNode:
        return SSHKeyNode(
            id=data.id,
            field_id=data.id,
            user_id=data.user_id,
            public_key=data.public_key,
            is_default=data.is_default,
        )
