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
        """Fire a Harbor webhook event.

        The server returns ``204 No Content`` on success, so this method
        bypasses ``typed_request()`` and returns *None* instead of a
        response model.
        """
        await self._client.fire_and_forget(
            "POST",
            "/container-registries/webhook/harbor",
            request=request,
        )
