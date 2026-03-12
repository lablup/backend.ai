from urllib.parse import urlencode

from ai.backend.client.v2.base_domain import BaseDomainClient
from ai.backend.common.container_registry import (
    CreateContainerRegistryRequestModel,
    ListContainerRegistriesResponseModel,
)
from ai.backend.common.dto.manager.container_registry.request import (
    HarborWebhookRequestModel,
    PatchContainerRegistryRequestModel,
)
from ai.backend.common.dto.manager.container_registry.response import (
    PatchContainerRegistryResponseModel,
)


class ContainerRegistryClient(BaseDomainClient):
    async def create(
        self,
        request: CreateContainerRegistryRequestModel,
    ) -> PatchContainerRegistryResponseModel:
        return await self._client.typed_request(
            "POST",
            "/container-registries/",
            request=request,
            response_model=PatchContainerRegistryResponseModel,
        )

    async def delete(
        self,
        registry_id: str,
    ) -> None:
        await self._client.typed_request_no_content(
            "DELETE",
            f"/container-registries/{registry_id}",
        )

    async def list_all(self) -> ListContainerRegistriesResponseModel:
        return await self._client.typed_request(
            "GET",
            "/container-registries/",
            response_model=ListContainerRegistriesResponseModel,
        )

    async def load(
        self,
        registry_name: str,
        project: str | None = None,
    ) -> ListContainerRegistriesResponseModel:
        params: dict[str, str] = {"registry": registry_name}
        if project is not None:
            params["project"] = project
        url = f"/container-registries/load?{urlencode(params)}"
        return await self._client.typed_request(
            "GET",
            url,
            response_model=ListContainerRegistriesResponseModel,
        )

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
