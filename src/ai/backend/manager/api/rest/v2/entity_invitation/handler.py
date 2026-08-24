"""REST v2 handler for entity invitations."""

from __future__ import annotations

from http import HTTPStatus
from typing import TYPE_CHECKING

from ai.backend.common.api_handlers import APIResponse, BodyParam, PathParam
from ai.backend.common.data.entity.entity_invitation import EntityInvitationID
from ai.backend.common.dto.manager.v2.entity_invitation.request import (
    CreateEntityInvitationInput,
    SearchEntityInvitationsInput,
)
from ai.backend.manager.api.rest.v2.path_params import InvitationIdPathParam

from .path_params import EntityTargetPathParam

if TYPE_CHECKING:
    from ai.backend.manager.api.adapters.entity_invitation.adapter import EntityInvitationAdapter


class V2EntityInvitationHandler:
    def __init__(self, *, adapter: EntityInvitationAdapter) -> None:
        self._adapter = adapter

    async def create(self, body: BodyParam[CreateEntityInvitationInput]) -> APIResponse:
        """Offer one entity to one address."""
        result = await self._adapter.create(body.parsed)
        return APIResponse.build(status_code=HTTPStatus.CREATED, response_model=result)

    async def get(self, path: PathParam[InvitationIdPathParam]) -> APIResponse:
        """Read one invitation from the side that offered it."""
        result = await self._adapter.get(EntityInvitationID(path.parsed.invitation_id))
        return APIResponse.build(status_code=HTTPStatus.OK, response_model=result)

    async def accept(self, path: PathParam[InvitationIdPathParam]) -> APIResponse:
        """Take what was offered."""
        result = await self._adapter.accept(EntityInvitationID(path.parsed.invitation_id))
        return APIResponse.build(status_code=HTTPStatus.OK, response_model=result)

    async def reject(self, path: PathParam[InvitationIdPathParam]) -> APIResponse:
        """Turn down what was offered."""
        result = await self._adapter.reject(EntityInvitationID(path.parsed.invitation_id))
        return APIResponse.build(status_code=HTTPStatus.OK, response_model=result)

    async def cancel(self, path: PathParam[InvitationIdPathParam]) -> APIResponse:
        """Withdraw the offer before it was answered."""
        result = await self._adapter.cancel(EntityInvitationID(path.parsed.invitation_id))
        return APIResponse.build(status_code=HTTPStatus.OK, response_model=result)

    async def search_received(self, body: BodyParam[SearchEntityInvitationsInput]) -> APIResponse:
        """The invitations addressed to the requester."""
        result = await self._adapter.search_received(body.parsed)
        return APIResponse.build(status_code=HTTPStatus.OK, response_model=result)

    async def search_sent(self, body: BodyParam[SearchEntityInvitationsInput]) -> APIResponse:
        """The invitations the requester sent."""
        result = await self._adapter.search_sent(body.parsed)
        return APIResponse.build(status_code=HTTPStatus.OK, response_model=result)

    async def search_by_target(
        self,
        path: PathParam[EntityTargetPathParam],
        body: BodyParam[SearchEntityInvitationsInput],
    ) -> APIResponse:
        """The invitations offering one entity."""
        result = await self._adapter.search_by_target(
            path.parsed.target_entity_type,
            EntityInvitationID(path.parsed.target_entity_id),
            body.parsed,
        )
        return APIResponse.build(status_code=HTTPStatus.OK, response_model=result)
