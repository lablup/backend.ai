from typing import Any, Mapping
from uuid import UUID

import aiohttp

from ai.backend.common.metrics.metric import LayerType
from ai.backend.manager.decorators.client_decorator import create_layer_aware_client_decorator

client_decorator = create_layer_aware_client_decorator(LayerType.WSPROXY_CLIENT)


class WSProxyClient:
    def __init__(self, address: str, token: str) -> None:
        self.address = address
        self.token = token

    @client_decorator()
    async def create_endpoint(
        self,
        endpoint_id: UUID,
        body: Mapping[str, Any],
    ) -> dict[str, Any]:
        async with aiohttp.ClientSession() as session:
            async with session.post(
                f"{self.address}/v2/endpoints/{endpoint_id}",
                json=body,
                headers={
                    "X-BackendAI-Token": self.token,
                },
            ) as resp:
                resp.raise_for_status()
                return await resp.json()

    @client_decorator()
    async def delete_endpoint(
        self,
        endpoint_id: UUID,
    ) -> None:
        async with aiohttp.ClientSession() as session:
            async with session.delete(
                f"{self.address}/v2/endpoints/{endpoint_id}",
                headers={
                    "X-BackendAI-Token": self.token,
                },
            ):
                pass
