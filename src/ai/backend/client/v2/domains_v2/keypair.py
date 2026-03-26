"""V2 REST SDK client for keypair operations."""

from __future__ import annotations

from typing import Final

from ai.backend.client.v2.base_domain import BaseDomainClient
from ai.backend.common.dto.manager.v2.keypair.request import (
    RevokeMyKeypairInput,
    SearchMyKeypairsRequest,
    SwitchMyMainAccessKeyInput,
    UpdateMyKeypairInput,
)
from ai.backend.common.dto.manager.v2.keypair.response import (
    IssueMyKeypairPayload,
    RevokeMyKeypairPayload,
    SearchMyKeypairsPayload,
    SwitchMyMainAccessKeyPayload,
    UpdateMyKeypairPayload,
)

_PATH: Final = "/v2/keypairs/my"


class V2KeypairClient(BaseDomainClient):
    """SDK client for ``/v2/keypairs/my`` endpoints."""

    async def search(
        self,
        request: SearchMyKeypairsRequest,
    ) -> SearchMyKeypairsPayload:
        """Search keypairs owned by the current user."""
        return await self._client.typed_request(
            "POST",
            f"{_PATH}/search",
            request=request,
            response_model=SearchMyKeypairsPayload,
        )

    async def issue(self) -> IssueMyKeypairPayload:
        """Issue a new keypair for the current user."""
        return await self._client.typed_request(
            "POST",
            f"{_PATH}/issue",
            response_model=IssueMyKeypairPayload,
        )

    async def revoke(self, request: RevokeMyKeypairInput) -> RevokeMyKeypairPayload:
        """Revoke a keypair owned by the current user."""
        return await self._client.typed_request(
            "POST",
            f"{_PATH}/revoke",
            request=request,
            response_model=RevokeMyKeypairPayload,
        )

    async def update(self, request: UpdateMyKeypairInput) -> UpdateMyKeypairPayload:
        """Update a keypair owned by the current user."""
        return await self._client.typed_request(
            "PATCH",
            _PATH,
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
            f"{_PATH}/switch-main",
            request=request,
            response_model=SwitchMyMainAccessKeyPayload,
        )
