from __future__ import annotations

from http import HTTPStatus
from uuid import UUID

from pydantic import Field

from ai.backend.common.api_handlers import APIResponse, BaseRequestModel, BodyParam, PathParam
from ai.backend.common.dto.manager.v2.deployment_revision_preset.request import (
    CreateDeploymentRevisionPresetInput,
    SearchDeploymentRevisionPresetsInput,
    UpdateDeploymentRevisionPresetInput,
)
from ai.backend.manager.api.adapters.deployment_revision_preset import (
    DeploymentRevisionPresetAdapter,
)


class PresetIdPathParam(BaseRequestModel):
    preset_id: UUID = Field(description="Deployment revision preset ID.")


class V2DeploymentRevisionPresetHandler:
    def __init__(self, *, adapter: DeploymentRevisionPresetAdapter) -> None:
        self._adapter = adapter

    async def search(
        self,
        body: BodyParam[SearchDeploymentRevisionPresetsInput],
    ) -> APIResponse:
        result = await self._adapter.search(body.parsed)
        return APIResponse.build(status_code=HTTPStatus.OK, response_model=result)

    async def create(
        self,
        body: BodyParam[CreateDeploymentRevisionPresetInput],
    ) -> APIResponse:
        result = await self._adapter.create(body.parsed)
        return APIResponse.build(status_code=HTTPStatus.CREATED, response_model=result)

    async def get(
        self,
        path: PathParam[PresetIdPathParam],
    ) -> APIResponse:
        result = await self._adapter.get(path.parsed.preset_id)
        return APIResponse.build(status_code=HTTPStatus.OK, response_model=result)

    async def update(
        self,
        path: PathParam[PresetIdPathParam],
        body: BodyParam[UpdateDeploymentRevisionPresetInput],
    ) -> APIResponse:
        merged = body.parsed.model_copy(update={"id": path.parsed.preset_id})
        result = await self._adapter.update(merged)
        return APIResponse.build(status_code=HTTPStatus.OK, response_model=result)

    async def delete(
        self,
        path: PathParam[PresetIdPathParam],
    ) -> APIResponse:
        result = await self._adapter.delete(path.parsed.preset_id)
        return APIResponse.build(status_code=HTTPStatus.OK, response_model=result)
