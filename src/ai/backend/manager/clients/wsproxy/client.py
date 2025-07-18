from typing import Any, Mapping
from uuid import UUID

import aiohttp


class WSProxyClient:
    def __init__(self, address: str, token: str) -> None:
        self.address = address
        self.token = token

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
