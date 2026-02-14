from ai.backend.client.v2.base_domain import BaseDomainClient
from ai.backend.common.dto.manager.registry.request import (
    CreateRegistryQuotaReq,
    DeleteRegistryQuotaReq,
    ReadRegistryQuotaReq,
    UpdateRegistryQuotaReq,
)
from ai.backend.common.dto.manager.registry.response import RegistryQuotaResponse


class GroupClient(BaseDomainClient):
    async def create_registry_quota(self, request: CreateRegistryQuotaReq) -> None:
        """Create a registry quota for a group.

        The server returns ``204 No Content`` on success.
        """
        await self._client.fire_and_forget(
            "POST",
            "/group/registry-quota",
            request=request,
        )

    async def read_registry_quota(self, request: ReadRegistryQuotaReq) -> RegistryQuotaResponse:
        return await self._client.typed_request(
            "GET",
            "/group/registry-quota",
            response_model=RegistryQuotaResponse,
            params={"group_id": request.group_id},
        )

    async def update_registry_quota(self, request: UpdateRegistryQuotaReq) -> None:
        """Update a registry quota for a group.

        The server returns ``204 No Content`` on success.
        """
        await self._client.fire_and_forget(
            "PATCH",
            "/group/registry-quota",
            request=request,
        )

    async def delete_registry_quota(self, request: DeleteRegistryQuotaReq) -> None:
        """Delete a registry quota for a group.

        The server returns ``204 No Content`` on success.
        """
        await self._client.fire_and_forget(
            "DELETE",
            "/group/registry-quota",
            request=request,
        )
