from __future__ import annotations

from http import HTTPStatus
from uuid import UUID

from pydantic import Field

from ai.backend.common.api_handlers import APIResponse, BaseRequestModel, BodyParam, PathParam
from ai.backend.common.dto.manager.v2.retention_policy.request import (
    CreateRetentionPolicyInput,
    SearchRetentionPoliciesInput,
    UpdateRetentionPolicyInput,
)
from ai.backend.common.identifier.retention_policy import RetentionPolicyID
from ai.backend.manager.api.adapters.retention_policy.adapter import RetentionPolicyAdapter


class RetentionPolicyIdPathParam(BaseRequestModel):
    policy_id: UUID = Field(description="Retention policy ID.")


class V2RetentionPolicyHandler:
    def __init__(self, *, adapter: RetentionPolicyAdapter) -> None:
        self._adapter = adapter

    async def admin_search(
        self,
        body: BodyParam[SearchRetentionPoliciesInput],
    ) -> APIResponse:
        result = await self._adapter.search(body.parsed)
        return APIResponse.build(status_code=HTTPStatus.OK, response_model=result)

    async def admin_create(
        self,
        body: BodyParam[CreateRetentionPolicyInput],
    ) -> APIResponse:
        result = await self._adapter.create(body.parsed)
        return APIResponse.build(status_code=HTTPStatus.CREATED, response_model=result)

    async def admin_get(
        self,
        path: PathParam[RetentionPolicyIdPathParam],
    ) -> APIResponse:
        result = await self._adapter.get(RetentionPolicyID(path.parsed.policy_id))
        return APIResponse.build(status_code=HTTPStatus.OK, response_model=result)

    async def admin_update(
        self,
        path: PathParam[RetentionPolicyIdPathParam],
        body: BodyParam[UpdateRetentionPolicyInput],
    ) -> APIResponse:
        merged = body.parsed.model_copy(update={"id": RetentionPolicyID(path.parsed.policy_id)})
        result = await self._adapter.update(merged)
        return APIResponse.build(status_code=HTTPStatus.OK, response_model=result)

    async def admin_delete(
        self,
        path: PathParam[RetentionPolicyIdPathParam],
    ) -> APIResponse:
        result = await self._adapter.delete(RetentionPolicyID(path.parsed.policy_id))
        return APIResponse.build(status_code=HTTPStatus.OK, response_model=result)

    async def admin_purge(
        self,
        path: PathParam[RetentionPolicyIdPathParam],
    ) -> APIResponse:
        result = await self._adapter.purge(RetentionPolicyID(path.parsed.policy_id))
        return APIResponse.build(status_code=HTTPStatus.OK, response_model=result)
