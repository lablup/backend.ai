from typing import Any
from uuid import UUID

import aiohttp

from ai.backend.common.metrics.metric import LayerType
from ai.backend.manager.decorators.client_decorator import create_layer_aware_client_decorator

from .types import CreateEndpointRequestBody

client_decorator = create_layer_aware_client_decorator(LayerType.WSPROXY_CLIENT)


class AppProxyClient:
    _client_session: aiohttp.ClientSession
    _address: str
    _token: str

    def __init__(self, client_session: aiohttp.ClientSession, address: str, token: str) -> None:
        self._client_session = client_session
        self._address = address
        self._token = token

    @client_decorator()
    async def create_endpoint(
        self,
        endpoint_id: UUID,
        body: CreateEndpointRequestBody,
    ) -> dict[str, Any]:
        async with self._client_session.post(
            f"/v2/endpoints/{endpoint_id}",
            json=body.model_dump(mode="json"),
            headers={
                "X-BackendAI-Token": self._token,
            },
        ) as resp:
            resp.raise_for_status()
            return await resp.json()

    @client_decorator()
    async def delete_endpoint(
        self,
        endpoint_id: UUID,
    ) -> None:
        async with self._client_session.delete(
            f"/v2/endpoints/{endpoint_id}",
            headers={
                "X-BackendAI-Token": self._token,
            },
        ):
            pass
