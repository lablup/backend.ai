from __future__ import annotations

from http import HTTPStatus
from uuid import UUID

from pydantic import Field

from ai.backend.common.api_handlers import APIResponse, BaseRequestModel, BodyParam, PathParam
from ai.backend.common.dto.manager.v2.runtime_variant.request import (
    CreateRuntimeVariantInput,
    SearchRuntimeVariantsInput,
    UpdateRuntimeVariantInput,
)
from ai.backend.manager.api.adapters.runtime_variant import RuntimeVariantAdapter


class VariantIdPathParam(BaseRequestModel):
    variant_id: UUID = Field(description="Runtime variant ID.")


class V2RuntimeVariantHandler:
    def __init__(self, *, adapter: RuntimeVariantAdapter) -> None:
        self._adapter = adapter

    async def search(
        self,
        body: BodyParam[SearchRuntimeVariantsInput],
    ) -> APIResponse:
        result = await self._adapter.search(body.parsed)
        return APIResponse.build(status_code=HTTPStatus.OK, response_model=result)

    async def create(
        self,
        body: BodyParam[CreateRuntimeVariantInput],
    ) -> APIResponse:
        result = await self._adapter.create(body.parsed)
        return APIResponse.build(status_code=HTTPStatus.CREATED, response_model=result)

    async def get(
        self,
        path: PathParam[VariantIdPathParam],
    ) -> APIResponse:
        result = await self._adapter.get(path.parsed.variant_id)
        return APIResponse.build(status_code=HTTPStatus.OK, response_model=result)

    async def update(
        self,
        path: PathParam[VariantIdPathParam],
        body: BodyParam[UpdateRuntimeVariantInput],
    ) -> APIResponse:
        merged = body.parsed.model_copy(update={"id": path.parsed.variant_id})
        result = await self._adapter.update(merged)
        return APIResponse.build(status_code=HTTPStatus.OK, response_model=result)

    async def delete(
        self,
        path: PathParam[VariantIdPathParam],
    ) -> APIResponse:
        result = await self._adapter.delete(path.parsed.variant_id)
        return APIResponse.build(status_code=HTTPStatus.OK, response_model=result)
