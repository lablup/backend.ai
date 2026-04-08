from __future__ import annotations

from uuid import UUID

from ai.backend.client.v2.base_domain import BaseDomainClient
from ai.backend.common.dto.manager.v2.deployment_revision_preset.request import (
    SearchDeploymentRevisionPresetsInput,
)
from ai.backend.common.dto.manager.v2.deployment_revision_preset.response import (
    SearchDeploymentRevisionPresetsPayload,
)
from ai.backend.common.dto.manager.v2.model_card.request import (
    CreateModelCardInput,
    DeleteModelCardsInput,
    DeployModelCardInput,
    SearchModelCardsInput,
    UpdateModelCardInput,
)
from ai.backend.common.dto.manager.v2.model_card.response import (
    CreateModelCardPayload,
    DeleteModelCardPayload,
    DeleteModelCardsPayload,
    DeployModelCardPayload,
    ModelCardNode,
    ScanProjectModelCardsPayload,
    SearchModelCardsPayload,
    UpdateModelCardPayload,
)

_PATH = "/v2/model-cards"


class V2ModelCardClient(BaseDomainClient):
    async def admin_search(self, request: SearchModelCardsInput) -> SearchModelCardsPayload:
        return await self._client.typed_request(
            "POST",
            f"{_PATH}/search",
            request=request,
            response_model=SearchModelCardsPayload,
        )

    async def project_search(
        self, project_id: UUID, request: SearchModelCardsInput
    ) -> SearchModelCardsPayload:
        return await self._client.typed_request(
            "POST",
            f"{_PATH}/projects/{project_id}/search",
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

    async def bulk_delete(self, request: DeleteModelCardsInput) -> DeleteModelCardsPayload:
        return await self._client.typed_request(
            "POST",
            f"{_PATH}/delete",
            request=request,
            response_model=DeleteModelCardsPayload,
        )

    async def scan_project(self, project_id: UUID) -> ScanProjectModelCardsPayload:
        return await self._client.typed_request(
            "POST",
            f"{_PATH}/projects/{project_id}/scan",
            response_model=ScanProjectModelCardsPayload,
        )

    async def deploy(self, card_id: UUID, request: DeployModelCardInput) -> DeployModelCardPayload:
        return await self._client.typed_request(
            "POST",
            f"{_PATH}/{card_id}/deploy",
            request=request,
            response_model=DeployModelCardPayload,
        )

    async def available_presets(
        self, card_id: UUID, request: SearchDeploymentRevisionPresetsInput
    ) -> SearchDeploymentRevisionPresetsPayload:
        return await self._client.typed_request(
            "POST",
            f"{_PATH}/{card_id}/available-presets/search",
            request=request,
            response_model=SearchDeploymentRevisionPresetsPayload,
        )
