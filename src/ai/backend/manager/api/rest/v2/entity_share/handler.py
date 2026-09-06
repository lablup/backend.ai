"""REST v2 handler for entity invitations."""

from __future__ import annotations

from http import HTTPStatus
from typing import TYPE_CHECKING

from ai.backend.common.api_handlers import APIResponse, BodyParam, PathParam
from ai.backend.common.data.entity.entity_share import EntityShareID
from ai.backend.common.dto.manager.v2.entity_share.request import (
    CreateEntityShareInput,
    MySearchEntitySharesInput,
    ScopedSearchEntitySharesInput,
)
from ai.backend.manager.api.rest.v2.path_params import ShareIdPathParam

if TYPE_CHECKING:
    from ai.backend.manager.api.adapters.entity_share.adapter import EntityShareAdapter


class V2EntityShareHandler:
    def __init__(self, *, adapter: EntityShareAdapter) -> None:
        self._adapter = adapter

    async def create(self, body: BodyParam[CreateEntityShareInput]) -> APIResponse:
        """Offer one entity to one address."""
        result = await self._adapter.create(body.parsed)
        return APIResponse.build(status_code=HTTPStatus.CREATED, response_model=result)

    async def get(self, path: PathParam[ShareIdPathParam]) -> APIResponse:
        """Read one invitation from the side that offered it."""
        result = await self._adapter.get(EntityShareID(path.parsed.share_id))
        return APIResponse.build(status_code=HTTPStatus.OK, response_model=result)

    async def accept(self, path: PathParam[ShareIdPathParam]) -> APIResponse:
        """Take what was offered."""
        result = await self._adapter.accept(EntityShareID(path.parsed.share_id))
        return APIResponse.build(status_code=HTTPStatus.OK, response_model=result)

    async def reject(self, path: PathParam[ShareIdPathParam]) -> APIResponse:
        """Turn down what was offered."""
        result = await self._adapter.reject(EntityShareID(path.parsed.share_id))
        return APIResponse.build(status_code=HTTPStatus.OK, response_model=result)

    async def revoke(self, path: PathParam[ShareIdPathParam]) -> APIResponse:
        """Take back what was lent."""
        result = await self._adapter.revoke(EntityShareID(path.parsed.share_id))
        return APIResponse.build(status_code=200, response_model=result)

    async def leave(self, path: PathParam[ShareIdPathParam]) -> APIResponse:
        """Give back what was taken."""
        result = await self._adapter.leave(EntityShareID(path.parsed.share_id))
        return APIResponse.build(status_code=200, response_model=result)

    async def cancel(self, path: PathParam[ShareIdPathParam]) -> APIResponse:
        """Withdraw the offer before it was answered."""
        result = await self._adapter.cancel(EntityShareID(path.parsed.share_id))
        return APIResponse.build(status_code=HTTPStatus.OK, response_model=result)

    async def my_search(self, body: BodyParam[MySearchEntitySharesInput]) -> APIResponse:
        """The shares the caller stands on a side of."""
        result = await self._adapter.my_search(body.parsed)
        return APIResponse.build(status_code=200, response_model=result)

    async def scoped_search(self, body: BodyParam[ScopedSearchEntitySharesInput]) -> APIResponse:
        """The invitations the named sides reach."""
        result = await self._adapter.scoped_search(body.parsed)
        return APIResponse.build(status_code=HTTPStatus.OK, response_model=result)
