from __future__ import annotations

import uuid

from ai.backend.client.v2.base_domain import BaseDomainClient
from ai.backend.common.dto.manager.auto_scaling_rule import (
    CreateAutoScalingRuleRequest,
    CreateAutoScalingRuleResponse,
    DeleteAutoScalingRuleRequest,
    DeleteAutoScalingRuleResponse,
    GetAutoScalingRuleResponse,
    SearchAutoScalingRulesRequest,
    SearchAutoScalingRulesResponse,
    UpdateAutoScalingRuleRequest,
    UpdateAutoScalingRuleResponse,
)


class AutoScalingRuleClient(BaseDomainClient):
    API_PREFIX = "/admin/auto-scaling-rules"

    async def create(
        self,
        request: CreateAutoScalingRuleRequest,
    ) -> CreateAutoScalingRuleResponse:
        return await self._client.typed_request(
            "POST",
            self.API_PREFIX,
            request=request,
            response_model=CreateAutoScalingRuleResponse,
        )

    async def get(
        self,
        rule_id: uuid.UUID,
    ) -> GetAutoScalingRuleResponse:
        return await self._client.typed_request(
            "GET",
            f"{self.API_PREFIX}/{rule_id}",
            response_model=GetAutoScalingRuleResponse,
        )

    async def search(
        self,
        request: SearchAutoScalingRulesRequest,
    ) -> SearchAutoScalingRulesResponse:
        return await self._client.typed_request(
            "POST",
            f"{self.API_PREFIX}/search",
            request=request,
            response_model=SearchAutoScalingRulesResponse,
        )

    async def update(
        self,
        rule_id: uuid.UUID,
        request: UpdateAutoScalingRuleRequest,
    ) -> UpdateAutoScalingRuleResponse:
        return await self._client.typed_request(
            "PATCH",
            f"{self.API_PREFIX}/{rule_id}",
            request=request,
            response_model=UpdateAutoScalingRuleResponse,
        )

    async def delete(
        self,
        request: DeleteAutoScalingRuleRequest,
    ) -> DeleteAutoScalingRuleResponse:
        return await self._client.typed_request(
            "POST",
            f"{self.API_PREFIX}/delete",
            request=request,
            response_model=DeleteAutoScalingRuleResponse,
        )
