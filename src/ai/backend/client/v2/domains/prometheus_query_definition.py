from __future__ import annotations

import uuid

from ai.backend.client.v2.base_domain import BaseDomainClient
from ai.backend.common.dto.manager.prometheus_query_preset import (
    CreateQueryDefinitionRequest,
    CreateQueryDefinitionResponse,
    DeleteQueryDefinitionResponse,
    ExecuteQueryDefinitionRequest,
    ExecuteQueryDefinitionResponse,
    GetQueryDefinitionResponse,
    ModifyQueryDefinitionRequest,
    ModifyQueryDefinitionResponse,
    SearchQueryDefinitionsRequest,
    SearchQueryDefinitionsResponse,
)


class PrometheusQueryDefinitionClient(BaseDomainClient):
    """Client for prometheus query definition management endpoints."""

    API_PREFIX = "/resource/prometheus-query-definitions"

    async def create(
        self,
        request: CreateQueryDefinitionRequest,
    ) -> CreateQueryDefinitionResponse:
        return await self._client.typed_request(
            "POST",
            self.API_PREFIX,
            request=request,
            response_model=CreateQueryDefinitionResponse,
        )

    async def search(
        self,
        request: SearchQueryDefinitionsRequest,
    ) -> SearchQueryDefinitionsResponse:
        return await self._client.typed_request(
            "POST",
            f"{self.API_PREFIX}/search",
            request=request,
            response_model=SearchQueryDefinitionsResponse,
        )

    async def get(
        self,
        definition_id: uuid.UUID,
    ) -> GetQueryDefinitionResponse:
        return await self._client.typed_request(
            "GET",
            f"{self.API_PREFIX}/{definition_id}",
            response_model=GetQueryDefinitionResponse,
        )

    async def modify(
        self,
        definition_id: uuid.UUID,
        request: ModifyQueryDefinitionRequest,
    ) -> ModifyQueryDefinitionResponse:
        return await self._client.typed_request(
            "PATCH",
            f"{self.API_PREFIX}/{definition_id}",
            request=request,
            response_model=ModifyQueryDefinitionResponse,
        )

    async def delete(
        self,
        definition_id: uuid.UUID,
    ) -> DeleteQueryDefinitionResponse:
        return await self._client.typed_request(
            "DELETE",
            f"{self.API_PREFIX}/{definition_id}",
            response_model=DeleteQueryDefinitionResponse,
        )

    async def execute(
        self,
        definition_id: uuid.UUID,
        request: ExecuteQueryDefinitionRequest,
    ) -> ExecuteQueryDefinitionResponse:
        return await self._client.typed_request(
            "POST",
            f"{self.API_PREFIX}/{definition_id}/execute",
            request=request,
            response_model=ExecuteQueryDefinitionResponse,
        )
