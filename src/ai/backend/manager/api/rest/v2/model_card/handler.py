from __future__ import annotations

from http import HTTPStatus
from uuid import UUID

from pydantic import Field

from ai.backend.common.api_handlers import (
    APIResponse,
    BaseRequestModel,
    BodyParam,
    PathParam,
    QueryParam,
)
from ai.backend.common.dto.manager.v2.deployment_revision_preset.request import (
    SearchDeploymentRevisionPresetsInput,
)
from ai.backend.common.dto.manager.v2.model_card.request import (
    BulkDeleteModelCardsInput,
    CreateModelCardInput,
    DeleteModelCardOptions,
    DeployModelCardInput,
    ScopedSearchModelCardsInput,
    SearchModelCardsInput,
    UpdateModelCardInput,
)
from ai.backend.common.dto.manager.v2.model_card.types import ModelCardScope
from ai.backend.common.dto.manager.v2.rbac.types import UUIDScope
from ai.backend.manager.api.adapters.model_card.adapter import ModelCardAdapter
from ai.backend.manager.api.rest.v2.path_params import ProjectIdPathParam
from ai.backend.manager.dto.context import UserContext


class CardIdPathParam(BaseRequestModel):
    card_id: UUID = Field(description="Model card ID.")


class V2ModelCardHandler:
    def __init__(self, *, adapter: ModelCardAdapter) -> None:
        self._adapter = adapter

    async def admin_search(
        self,
        body: BodyParam[SearchModelCardsInput],
    ) -> APIResponse:
        result = await self._adapter.admin_search(body.parsed)
        return APIResponse.build(status_code=HTTPStatus.OK, response_model=result)

    async def my_search(
        self,
        user_ctx: UserContext,
        body: BodyParam[SearchModelCardsInput],
    ) -> APIResponse:
        """Search the model cards the current user holds through membership."""
        result = await self._adapter.scoped_search(
            ScopedSearchModelCardsInput(
                scope=ModelCardScope(user=[UUIDScope(value=user_ctx.user_uuid)]),
                usage=body.parsed.usage,
                filter=body.parsed.filter,
                order=body.parsed.order,
                first=body.parsed.first,
                after=body.parsed.after,
                last=body.parsed.last,
                before=body.parsed.before,
                limit=body.parsed.limit,
                offset=body.parsed.offset,
            )
        )
        return APIResponse.build(status_code=HTTPStatus.OK, response_model=result)

    async def scoped_search(
        self,
        body: BodyParam[ScopedSearchModelCardsInput],
    ) -> APIResponse:
        """Search the model cards the named scopes reach, combined with OR."""
        result = await self._adapter.scoped_search(body.parsed)
        return APIResponse.build(status_code=HTTPStatus.OK, response_model=result)

    async def project_search(
        self,
        path: PathParam[ProjectIdPathParam],
        body: BodyParam[SearchModelCardsInput],
    ) -> APIResponse:
        result = await self._adapter.project_search(path.parsed.project_id, body.parsed)
        return APIResponse.build(status_code=HTTPStatus.OK, response_model=result)

    async def create(
        self,
        body: BodyParam[CreateModelCardInput],
    ) -> APIResponse:
        result = await self._adapter.create(body.parsed)
        return APIResponse.build(status_code=HTTPStatus.CREATED, response_model=result)

    async def get(
        self,
        path: PathParam[CardIdPathParam],
    ) -> APIResponse:
        result = await self._adapter.get(path.parsed.card_id)
        return APIResponse.build(status_code=HTTPStatus.OK, response_model=result)

    async def update(
        self,
        path: PathParam[CardIdPathParam],
        body: BodyParam[UpdateModelCardInput],
    ) -> APIResponse:
        merged = body.parsed.model_copy(update={"id": path.parsed.card_id})
        result = await self._adapter.update(merged)
        return APIResponse.build(status_code=HTTPStatus.OK, response_model=result)

    async def delete(
        self,
        path: PathParam[CardIdPathParam],
        query: QueryParam[DeleteModelCardOptions],
    ) -> APIResponse:
        result = await self._adapter.delete(path.parsed.card_id, options=query.parsed)
        return APIResponse.build(status_code=HTTPStatus.OK, response_model=result)

    async def admin_bulk_delete(
        self,
        body: BodyParam[BulkDeleteModelCardsInput],
    ) -> APIResponse:
        result = await self._adapter.admin_bulk_delete(
            body.parsed, body.parsed.options or DeleteModelCardOptions()
        )
        return APIResponse.build(status_code=HTTPStatus.OK, response_model=result)

    async def scan_project(
        self,
        path: PathParam[ProjectIdPathParam],
    ) -> APIResponse:
        result = await self._adapter.scan_project(path.parsed.project_id)
        return APIResponse.build(status_code=HTTPStatus.OK, response_model=result)

    async def deploy(
        self,
        path: PathParam[CardIdPathParam],
        body: BodyParam[DeployModelCardInput],
    ) -> APIResponse:
        result = await self._adapter.deploy(path.parsed.card_id, body.parsed)
        return APIResponse.build(status_code=HTTPStatus.CREATED, response_model=result)

    async def available_presets(
        self,
        path: PathParam[CardIdPathParam],
        body: BodyParam[SearchDeploymentRevisionPresetsInput],
    ) -> APIResponse:
        result = await self._adapter.available_presets(path.parsed.card_id, body.parsed)
        return APIResponse.build(status_code=HTTPStatus.OK, response_model=result)
