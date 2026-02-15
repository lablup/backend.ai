from ai.backend.client.v2.base_domain import BaseDomainClient
from ai.backend.common.dto.manager.registry.request import (
    CreateRegistryQuotaReq,
    DeleteRegistryQuotaReq,
    ReadRegistryQuotaReq,
    UpdateRegistryQuotaReq,
)
from ai.backend.common.dto.manager.registry.response import RegistryQuotaResponse

_BASE_PATH = "/group"


class GroupClient(BaseDomainClient):
    async def create_registry_quota(
        self,
        request: CreateRegistryQuotaReq,
    ) -> None:
        await self._client.typed_request_no_content(
            "POST",
            f"{_BASE_PATH}/registry-quota",
            request=request,
        )

    async def read_registry_quota(
        self,
        request: ReadRegistryQuotaReq,
    ) -> RegistryQuotaResponse:
        params = {k: str(v) for k, v in request.model_dump(exclude_none=True).items()}
        return await self._client.typed_request(
            "GET",
            f"{_BASE_PATH}/registry-quota",
            response_model=RegistryQuotaResponse,
            params=params,
        )

    async def update_registry_quota(
        self,
        request: UpdateRegistryQuotaReq,
    ) -> None:
        await self._client.typed_request_no_content(
            "PATCH",
            f"{_BASE_PATH}/registry-quota",
            request=request,
        )

    async def delete_registry_quota(
        self,
        request: DeleteRegistryQuotaReq,
    ) -> None:
        await self._client.typed_request_no_content(
            "DELETE",
            f"{_BASE_PATH}/registry-quota",
            request=request,
        )
