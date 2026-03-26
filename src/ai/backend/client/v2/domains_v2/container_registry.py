"""V2 REST SDK client for the container registry domain."""

from __future__ import annotations

from ai.backend.client.v2.base_domain import BaseDomainClient
from ai.backend.common.dto.manager.v2.container_registry.request import (
    AdminSearchContainerRegistriesInput,
)
from ai.backend.common.dto.manager.v2.container_registry.response import (
    AdminSearchContainerRegistriesPayload,
)

_PATH = "/v2/container-registries"


class V2ContainerRegistryClient(BaseDomainClient):
    """SDK client for the ``/v2/container-registries`` REST endpoints."""

    async def admin_search(
        self,
        request: AdminSearchContainerRegistriesInput,
    ) -> AdminSearchContainerRegistriesPayload:
        """Search container registries with admin scope."""
        return await self._client.typed_request(
            "POST",
            f"{_PATH}/search",
            request=request,
            response_model=AdminSearchContainerRegistriesPayload,
        )
