from ai.backend.client.v2.base_domain import BaseDomainClient
from ai.backend.common.container_registry import (
    PatchContainerRegistryRequestModel,
    PatchContainerRegistryResponseModel,
)


class ContainerRegistryClient(BaseDomainClient):
    async def patch(
        self,
        registry_id: str,
        request: PatchContainerRegistryRequestModel,
    ) -> PatchContainerRegistryResponseModel:
        return await self._client.typed_request(
            "PATCH",
            f"/container-registries/{registry_id}",
            request=request,
            response_model=PatchContainerRegistryResponseModel,
        )
