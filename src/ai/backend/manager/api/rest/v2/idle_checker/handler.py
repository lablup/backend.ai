"""REST v2 handler for idle checker operations."""

from __future__ import annotations

from http import HTTPStatus
from typing import TYPE_CHECKING

from ai.backend.common.api_handlers import APIResponse, BodyParam, PathParam
from ai.backend.common.dto.manager.v2.idle_checker.request import (
    CreateIdleCheckerInput,
    PurgeIdleCheckerInput,
    SearchIdleCheckersInput,
    UpdateIdleCheckerInput,
)
from ai.backend.common.identifier.idle_checker import IdleCheckerID
from ai.backend.manager.api.rest.v2.path_params import IdleCheckerIdPathParam

if TYPE_CHECKING:
    from ai.backend.manager.api.adapters.idle_checker.adapter import IdleCheckerAdapter


class V2IdleCheckerHandler:
    """REST v2 handler for idle checker operations (admin-only)."""

    def __init__(self, *, adapter: IdleCheckerAdapter) -> None:
        self._adapter = adapter

    async def admin_create(
        self,
        body: BodyParam[CreateIdleCheckerInput],
    ) -> APIResponse:
        result = await self._adapter.admin_create(body.parsed)
        return APIResponse.build(status_code=HTTPStatus.CREATED, response_model=result)

    async def admin_search(
        self,
        body: BodyParam[SearchIdleCheckersInput],
    ) -> APIResponse:
        result = await self._adapter.admin_search(body.parsed)
        return APIResponse.build(status_code=HTTPStatus.OK, response_model=result)

    async def admin_update(
        self,
        path: PathParam[IdleCheckerIdPathParam],
        body: BodyParam[UpdateIdleCheckerInput],
    ) -> APIResponse:
        input_ = body.parsed.model_copy(update={"id": IdleCheckerID(path.parsed.idle_checker_id)})
        result = await self._adapter.admin_update(input_)
        return APIResponse.build(status_code=HTTPStatus.OK, response_model=result)

    async def admin_purge(
        self,
        path: PathParam[IdleCheckerIdPathParam],
    ) -> APIResponse:
        result = await self._adapter.admin_purge(
            PurgeIdleCheckerInput(id=IdleCheckerID(path.parsed.idle_checker_id))
        )
        return APIResponse.build(status_code=HTTPStatus.OK, response_model=result)
