from ai.backend.client.v2.base_domain import BaseDomainClient
from ai.backend.common.dto.manager.container_registry.request import (
    HarborWebhookRequestModel,
    PatchContainerRegistryRequestModel,
)
from ai.backend.common.dto.manager.container_registry.response import (
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

    async def handle_harbor_webhook(
        self,
        request: HarborWebhookRequestModel,
    ) -> None:
        await self._client.typed_request_no_content(
            "POST",
            "/container-registries/webhook/harbor",
            request=request,
        )
