"""V2 SDK client for idle checker operations."""

from __future__ import annotations

from typing import Final

from ai.backend.client.v2.base_domain import BaseDomainClient
from ai.backend.common.dto.manager.v2.idle_checker.request import (
    CreateIdleCheckerInput,
    SearchIdleCheckersInput,
    UpdateIdleCheckerInput,
)
from ai.backend.common.dto.manager.v2.idle_checker.response import (
    CreateIdleCheckerPayload,
    PurgeIdleCheckerPayload,
    SearchIdleCheckerPayload,
    UpdateIdleCheckerPayload,
)
from ai.backend.common.identifier.idle_checker import IdleCheckerID

_PATH: Final = "/v2/idle-checkers"


class V2IdleCheckerClient(BaseDomainClient):
    """SDK client for idle checker operations (admin-only)."""

    async def admin_create(
        self,
        request: CreateIdleCheckerInput,
    ) -> CreateIdleCheckerPayload:
        return await self._client.typed_request(
            "POST",
            f"{_PATH}/",
            request=request,
            response_model=CreateIdleCheckerPayload,
        )

    async def admin_search(
        self,
        request: SearchIdleCheckersInput,
    ) -> SearchIdleCheckerPayload:
        return await self._client.typed_request(
            "POST",
            f"{_PATH}/search",
            request=request,
            response_model=SearchIdleCheckerPayload,
        )

    async def admin_update(
        self,
        idle_checker_id: IdleCheckerID,
        request: UpdateIdleCheckerInput,
    ) -> UpdateIdleCheckerPayload:
        return await self._client.typed_request(
            "PATCH",
            f"{_PATH}/{idle_checker_id}",
            request=request,
            response_model=UpdateIdleCheckerPayload,
        )

    async def admin_purge(
        self,
        idle_checker_id: IdleCheckerID,
    ) -> PurgeIdleCheckerPayload:
        return await self._client.typed_request(
            "DELETE",
            f"{_PATH}/{idle_checker_id}",
            response_model=PurgeIdleCheckerPayload,
        )
