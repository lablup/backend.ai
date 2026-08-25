"""V2 REST SDK client for keypair operations."""

from __future__ import annotations

from typing import Final

from ai.backend.client.v2.base_domain import BaseDomainClient
from ai.backend.common.dto.manager.v2.keypair.request import (
    AdminCreateKeypairInput,
    AdminRegisterSSHKeypairInput,
    AdminSearchKeypairsInput,
    AdminUpdateKeypairInput,
    RevokeMyKeypairInput,
    SearchMyKeypairsRequest,
    SwitchMyMainAccessKeyInput,
    UpdateMyKeypairInput,
)
from ai.backend.common.dto.manager.v2.keypair.response import (
    AdminCreateKeypairPayload,
    AdminDeleteKeypairPayload,
    AdminDeleteSSHKeypairPayload,
    AdminGetSSHKeypairPayload,
    AdminRegisterSSHKeypairPayload,
    AdminSearchKeypairsPayload,
    AdminUpdateKeypairPayload,
    IssueMyKeypairPayload,
    KeypairNode,
    RevokeMyKeypairPayload,
    SearchMyKeypairsPayload,
    SwitchMyMainAccessKeyPayload,
    UpdateMyKeypairPayload,
)

_MY_PATH: Final = "/v2/keypairs/my"
_ADMIN_PATH: Final = "/v2/keypairs"


class V2KeypairClient(BaseDomainClient):
    """SDK client for ``/v2/keypairs`` endpoints."""

    # ------------------------------------------------------------------ self-service (my)

    async def search(
        self,
        request: SearchMyKeypairsRequest,
    ) -> SearchMyKeypairsPayload:
        """Search keypairs owned by the current user."""
        return await self._client.typed_request(
            "POST",
            f"{_MY_PATH}/search",
            request=request,
            response_model=SearchMyKeypairsPayload,
        )

    async def issue(self) -> IssueMyKeypairPayload:
        """Issue a new keypair for the current user."""
        return await self._client.typed_request(
            "POST",
            f"{_MY_PATH}/issue",
            response_model=IssueMyKeypairPayload,
        )

    async def revoke(self, request: RevokeMyKeypairInput) -> RevokeMyKeypairPayload:
        """Revoke a keypair owned by the current user."""
        return await self._client.typed_request(
            "POST",
            f"{_MY_PATH}/revoke",
            request=request,
            response_model=RevokeMyKeypairPayload,
        )

    async def update(self, request: UpdateMyKeypairInput) -> UpdateMyKeypairPayload:
        """Update a keypair owned by the current user."""
        return await self._client.typed_request(
            "PATCH",
            _MY_PATH,
            request=request,
            response_model=UpdateMyKeypairPayload,
        )

    async def switch_main(
        self,
        request: SwitchMyMainAccessKeyInput,
    ) -> SwitchMyMainAccessKeyPayload:
        """Switch the main access key for the current user."""
        return await self._client.typed_request(
            "POST",
            f"{_MY_PATH}/switch-main",
            request=request,
            response_model=SwitchMyMainAccessKeyPayload,
        )

    # ------------------------------------------------------------------ admin

    async def admin_search(
        self,
        request: AdminSearchKeypairsInput,
    ) -> AdminSearchKeypairsPayload:
        """Search all keypairs (admin only)."""
        return await self._client.typed_request(
            "POST",
            f"{_ADMIN_PATH}/search",
            request=request,
            response_model=AdminSearchKeypairsPayload,
        )

    async def admin_get(self, access_key: str) -> KeypairNode:
        """Get a single keypair by access key (admin only)."""
        return await self._client.typed_request(
            "GET",
            f"{_ADMIN_PATH}/{access_key}",
            response_model=KeypairNode,
        )

    async def admin_create(self, request: AdminCreateKeypairInput) -> AdminCreateKeypairPayload:
        """Create a keypair for a user (admin only)."""
        return await self._client.typed_request(
            "POST",
            _ADMIN_PATH,
            request=request,
            response_model=AdminCreateKeypairPayload,
        )

    async def admin_update(self, request: AdminUpdateKeypairInput) -> AdminUpdateKeypairPayload:
        """Update a keypair (admin only)."""
        return await self._client.typed_request(
            "PATCH",
            _ADMIN_PATH,
            request=request,
            response_model=AdminUpdateKeypairPayload,
        )

    async def admin_delete(self, access_key: str) -> AdminDeleteKeypairPayload:
        """Delete a keypair (admin only)."""
        return await self._client.typed_request(
            "DELETE",
            f"{_ADMIN_PATH}/{access_key}",
            response_model=AdminDeleteKeypairPayload,
        )

    # ------------------------------------------------------------------ admin SSH keypair

    async def admin_register_ssh_keypair(
        self,
        request: AdminRegisterSSHKeypairInput,
    ) -> AdminRegisterSSHKeypairPayload:
        """Register (overwrite) a user's SSH keypair (admin only)."""
        return await self._client.typed_request(
            "POST",
            f"{_ADMIN_PATH}/ssh",
            request=request,
            response_model=AdminRegisterSSHKeypairPayload,
        )

    async def admin_get_ssh_keypair(self, access_key: str) -> AdminGetSSHKeypairPayload:
        """Get a user's SSH public key (admin only)."""
        return await self._client.typed_request(
            "GET",
            f"{_ADMIN_PATH}/{access_key}/ssh",
            response_model=AdminGetSSHKeypairPayload,
        )

    async def admin_delete_ssh_keypair(self, access_key: str) -> AdminDeleteSSHKeypairPayload:
        """Clear a user's SSH keypair (admin only)."""
        return await self._client.typed_request(
            "DELETE",
            f"{_ADMIN_PATH}/{access_key}/ssh",
            response_model=AdminDeleteSSHKeypairPayload,
        )
