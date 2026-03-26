"""REST v2 handler for self-service keypair operations."""

from __future__ import annotations

import logging
from http import HTTPStatus
from typing import TYPE_CHECKING, Final

from ai.backend.common.api_handlers import APIResponse, BodyParam
from ai.backend.common.dto.manager.pagination import PaginationInfo
from ai.backend.common.dto.manager.v2.keypair.request import (
    RevokeMyKeypairInput,
    SearchMyKeypairsRequest,
    SwitchMyMainAccessKeyInput,
    UpdateMyKeypairInput,
)
from ai.backend.common.dto.manager.v2.keypair.response import SearchMyKeypairsPayload
from ai.backend.logging import BraceStyleAdapter
from ai.backend.manager.dto.context import UserContext

if TYPE_CHECKING:
    from ai.backend.manager.api.adapters.user import UserAdapter

log: Final = BraceStyleAdapter(logging.getLogger(__spec__.name))


class V2KeypairHandler:
    """REST v2 handler for self-service keypair operations."""

    def __init__(self, *, adapter: UserAdapter) -> None:
        self._adapter = adapter

    async def search(
        self,
        body: BodyParam[SearchMyKeypairsRequest],
    ) -> APIResponse:
        """Search keypairs owned by the current user."""
        search_result = await self._adapter.search_my_keypairs(body.parsed)
        payload = SearchMyKeypairsPayload(
            items=search_result.items,
            pagination=PaginationInfo(
                total=search_result.total_count,
                offset=body.parsed.offset or 0,
                limit=body.parsed.limit,
            ),
        )
        return APIResponse.build(status_code=HTTPStatus.OK, response_model=payload)

    async def issue(
        self,
        ctx: UserContext,
    ) -> APIResponse:
        """Issue a new keypair for the current user."""
        result = await self._adapter.issue_my_keypair(ctx.user_uuid)
        return APIResponse.build(status_code=HTTPStatus.CREATED, response_model=result)

    async def revoke(
        self,
        body: BodyParam[RevokeMyKeypairInput],
        ctx: UserContext,
    ) -> APIResponse:
        """Revoke a keypair owned by the current user."""
        result = await self._adapter.revoke_my_keypair(ctx.user_uuid, body.parsed.access_key)
        return APIResponse.build(status_code=HTTPStatus.OK, response_model=result)

    async def update(
        self,
        body: BodyParam[UpdateMyKeypairInput],
        ctx: UserContext,
    ) -> APIResponse:
        """Update a keypair owned by the current user."""
        result = await self._adapter.update_my_keypair(
            ctx.user_uuid, body.parsed.access_key, body.parsed.is_active
        )
        return APIResponse.build(status_code=HTTPStatus.OK, response_model=result)

    async def switch_main(
        self,
        body: BodyParam[SwitchMyMainAccessKeyInput],
        ctx: UserContext,
    ) -> APIResponse:
        """Switch the main access key for the current user."""
        result = await self._adapter.switch_my_main_access_key(
            ctx.user_uuid, body.parsed.access_key
        )
        return APIResponse.build(status_code=HTTPStatus.OK, response_model=result)
