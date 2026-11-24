"""V2 SDK client for the SSH key domain."""

from __future__ import annotations

from typing import Final

from ai.backend.client.v2.base_domain import BaseDomainClient
from ai.backend.common.data.entity.ssh_keypair import SSHKeypairID
from ai.backend.common.dto.manager.v2.ssh_key.request import (
    MySearchSSHKeysInput,
    MyUploadSSHKeyInput,
)
from ai.backend.common.dto.manager.v2.ssh_key.response import SearchSSHKeysPayload, SSHKeyNode

_PATH: Final = "/v2/ssh-keys"


class V2SSHKeyClient(BaseDomainClient):
    """SDK client for uploading, reading and searching SSH keys and switching the default."""

    async def my_upload(self, request: MyUploadSSHKeyInput) -> SSHKeyNode:
        """Upload a public key to the current user."""
        return await self._client.typed_request(
            "POST",
            f"{_PATH}/my/upload",
            request=request,
            response_model=SSHKeyNode,
        )

    async def switch_default(self, ssh_key_id: SSHKeypairID) -> SSHKeyNode:
        """Make an SSH key the default of its owner."""
        return await self._client.typed_request(
            "POST",
            f"{_PATH}/{ssh_key_id}/switch-default",
            response_model=SSHKeyNode,
        )

    async def get(self, ssh_key_id: SSHKeypairID) -> SSHKeyNode:
        """Read one SSH key."""
        return await self._client.typed_request(
            "GET", f"{_PATH}/{ssh_key_id}", response_model=SSHKeyNode
        )

    async def my_search(self, request: MySearchSSHKeysInput) -> SearchSSHKeysPayload:
        """Search the caller's own SSH keys."""
        return await self._client.typed_request(
            "POST",
            f"{_PATH}/my/search",
            request=request,
            response_model=SearchSSHKeysPayload,
        )
