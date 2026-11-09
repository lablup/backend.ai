from __future__ import annotations

from http import HTTPStatus
from uuid import UUID

from pydantic import Field

from ai.backend.common.api_handlers import APIResponse, BaseRequestModel, BodyParam, PathParam
from ai.backend.common.dto.manager.v2.runtime_variant_preset.request import (
    CreateRuntimeVariantPresetInput,
    PartialBulkPurgeRuntimeVariantPresetsInput,
    PartialBulkUpdateRuntimeVariantPresetsInput,
    SearchRuntimeVariantPresetsInput,
    UpdateRuntimeVariantPresetInput,
)
from ai.backend.manager.api.adapters.runtime_variant_preset.adapter import (
    RuntimeVariantPresetAdapter,
)


class PresetIdPathParam(BaseRequestModel):
    preset_id: UUID = Field(description="Runtime variant preset ID.")


class V2RuntimeVariantPresetHandler:
    def __init__(self, *, adapter: RuntimeVariantPresetAdapter) -> None:
        self._adapter = adapter

    async def search(
        self,
        body: BodyParam[SearchRuntimeVariantPresetsInput],
    ) -> APIResponse:
        result = await self._adapter.search(body.parsed)
        return APIResponse.build(status_code=HTTPStatus.OK, response_model=result)

    async def create(
        self,
        body: BodyParam[CreateRuntimeVariantPresetInput],
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
        body: BodyParam[UpdateRuntimeVariantPresetInput],
    ) -> APIResponse:
        merged = body.parsed.model_copy(update={"id": path.parsed.preset_id})
        result = await self._adapter.update(merged)
        return APIResponse.build(status_code=HTTPStatus.OK, response_model=result)

    async def purge(
        self,
        path: PathParam[PresetIdPathParam],
    ) -> APIResponse:
        """Purge a runtime variant preset."""
        result = await self._adapter.purge(path.parsed.preset_id)
        return APIResponse.build(status_code=HTTPStatus.OK, response_model=result)

    async def partial_bulk_update(
        self,
        body: BodyParam[PartialBulkUpdateRuntimeVariantPresetsInput],
    ) -> APIResponse:
        """Update several runtime variant presets, answering for each one."""
        result = await self._adapter.partial_bulk_update(body.parsed)
        return APIResponse.build(status_code=HTTPStatus.OK, response_model=result)

    async def partial_bulk_purge(
        self,
        body: BodyParam[PartialBulkPurgeRuntimeVariantPresetsInput],
    ) -> APIResponse:
        """Purge several runtime variant presets, answering for each one."""
        result = await self._adapter.partial_bulk_purge(body.parsed)
        return APIResponse.build(status_code=HTTPStatus.OK, response_model=result)
