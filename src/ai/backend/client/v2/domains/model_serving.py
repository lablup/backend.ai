from __future__ import annotations

import uuid
from typing import Any

from pydantic import TypeAdapter

from ai.backend.client.v2.base_domain import BaseDomainClient
from ai.backend.client.v2.exceptions import map_status_to_exception
from ai.backend.common.dto.manager.model_serving import (
    CompactServeInfoModel,
    ErrorListResponseModel,
    NewServiceRequestModel,
    RuntimeInfoModel,
    ScaleRequestModel,
    ScaleResponseModel,
    SearchServicesRequestModel,
    SearchServicesResponseModel,
    ServeInfoModel,
    SuccessResponseModel,
    TokenRequestModel,
    TokenResponseModel,
    TryStartResponseModel,
    UpdateRouteRequestModel,
)

_list_adapter: TypeAdapter[list[CompactServeInfoModel]] = TypeAdapter(list[CompactServeInfoModel])


class ModelServingClient(BaseDomainClient):
    API_PREFIX = "/services"

    async def list_serve(
        self,
        name: str | None = None,
    ) -> list[CompactServeInfoModel]:
        params: dict[str, str] | None = None
        if name is not None:
            params = {"name": name}
        raw: Any = await self._client._request("GET", self.API_PREFIX, params=params)
        return _list_adapter.validate_python(raw)

    async def search_services(
        self,
        request: SearchServicesRequestModel,
    ) -> SearchServicesResponseModel:
        return await self._client.typed_request(
            "POST",
            f"{self.API_PREFIX}/_/search",
            request=request,
            response_model=SearchServicesResponseModel,
        )

    async def get_info(self, service_id: uuid.UUID) -> ServeInfoModel:
        return await self._client.typed_request(
            "GET",
            f"{self.API_PREFIX}/{service_id}",
            response_model=ServeInfoModel,
        )

    async def create(self, request: NewServiceRequestModel) -> ServeInfoModel:
        return await self._client.typed_request(
            "POST",
            self.API_PREFIX,
            request=request,
            response_model=ServeInfoModel,
        )

    async def try_start(self, request: NewServiceRequestModel) -> TryStartResponseModel:
        return await self._client.typed_request(
            "POST",
            f"{self.API_PREFIX}/_/try",
            request=request,
            response_model=TryStartResponseModel,
        )

    async def delete(self, service_id: uuid.UUID) -> SuccessResponseModel:
        return await self._client.typed_request(
            "DELETE",
            f"{self.API_PREFIX}/{service_id}",
            response_model=SuccessResponseModel,
        )

    async def sync(self, service_id: uuid.UUID) -> SuccessResponseModel:
        return await self._client.typed_request(
            "POST",
            f"{self.API_PREFIX}/{service_id}/sync",
            response_model=SuccessResponseModel,
        )

    async def scale(
        self,
        service_id: uuid.UUID,
        request: ScaleRequestModel,
    ) -> ScaleResponseModel:
        return await self._client.typed_request(
            "POST",
            f"{self.API_PREFIX}/{service_id}/scale",
            request=request,
            response_model=ScaleResponseModel,
        )

    async def update_route(
        self,
        service_id: uuid.UUID,
        route_id: uuid.UUID,
        request: UpdateRouteRequestModel,
    ) -> SuccessResponseModel:
        return await self._client.typed_request(
            "PUT",
            f"{self.API_PREFIX}/{service_id}/routings/{route_id}",
            request=request,
            response_model=SuccessResponseModel,
        )

    async def delete_route(
        self,
        service_id: uuid.UUID,
        route_id: uuid.UUID,
    ) -> SuccessResponseModel:
        return await self._client.typed_request(
            "DELETE",
            f"{self.API_PREFIX}/{service_id}/routings/{route_id}",
            response_model=SuccessResponseModel,
        )

    async def generate_token(
        self,
        service_id: uuid.UUID,
        request: TokenRequestModel,
    ) -> TokenResponseModel:
        return await self._client.typed_request(
            "POST",
            f"{self.API_PREFIX}/{service_id}/token",
            request=request,
            response_model=TokenResponseModel,
        )

    async def list_errors(self, service_id: uuid.UUID) -> ErrorListResponseModel:
        return await self._client.typed_request(
            "GET",
            f"{self.API_PREFIX}/{service_id}/errors",
            response_model=ErrorListResponseModel,
        )

    async def clear_error(self, service_id: uuid.UUID) -> None:
        method = "POST"
        path = f"{self.API_PREFIX}/{service_id}/errors/clear"
        content_type = "application/json"
        rel_url = "/" + path.lstrip("/")
        headers = self._client._sign(method, rel_url, content_type)
        url = self._client._build_url(path)
        async with self._client._session.request(method, url, headers=headers) as resp:
            if resp.status >= 400:
                try:
                    data = await resp.json()
                except Exception:
                    data = await resp.text()
                raise map_status_to_exception(resp.status, resp.reason or "", data)

    async def list_supported_runtimes(self) -> RuntimeInfoModel:
        return await self._client.typed_request(
            "GET",
            f"{self.API_PREFIX}/_/runtimes",
            response_model=RuntimeInfoModel,
        )
