from __future__ import annotations

from uuid import UUID

from ai.backend.client.v2.base_domain import BaseDomainClient
from ai.backend.common.dto.manager.v2.model_card.request import (
    CreateModelCardInput,
    SearchModelCardsInput,
    UpdateModelCardInput,
)
from ai.backend.common.dto.manager.v2.model_card.response import (
    CreateModelCardPayload,
    DeleteModelCardPayload,
    ModelCardNode,
    SearchModelCardsPayload,
    UpdateModelCardPayload,
)

_PATH = "/v2/model-cards"


class V2ModelCardClient(BaseDomainClient):
    async def search(self, request: SearchModelCardsInput) -> SearchModelCardsPayload:
        return await self._client.typed_request(
            "POST",
            f"{_PATH}/search",
            request=request,
            response_model=SearchModelCardsPayload,
        )

    async def get(self, card_id: UUID) -> ModelCardNode:
        return await self._client.typed_request(
            "GET",
            f"{_PATH}/{card_id}",
            response_model=ModelCardNode,
        )

    async def create(self, request: CreateModelCardInput) -> CreateModelCardPayload:
        return await self._client.typed_request(
            "POST",
            _PATH,
            request=request,
            response_model=CreateModelCardPayload,
        )

    async def update(self, card_id: UUID, request: UpdateModelCardInput) -> UpdateModelCardPayload:
        return await self._client.typed_request(
            "PATCH",
            f"{_PATH}/{card_id}",
            request=request,
            response_model=UpdateModelCardPayload,
        )

    async def delete(self, card_id: UUID) -> DeleteModelCardPayload:
        return await self._client.typed_request(
            "DELETE",
            f"{_PATH}/{card_id}",
            response_model=DeleteModelCardPayload,
        )
