from ai.backend.client.v2.base_domain import BaseDomainClient
from ai.backend.common.container_registry import (
    PatchContainerRegistryRequestModel,
    PatchContainerRegistryResponseModel,
)
from ai.backend.common.dto.manager.registry.request import HarborWebhookRequestModel


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
