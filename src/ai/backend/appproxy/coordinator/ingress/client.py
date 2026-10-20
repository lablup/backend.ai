from __future__ import annotations

from collections.abc import Sequence

import aiohttp

from ai.backend.appproxy.common.config import SecretConfig
from ai.backend.appproxy.coordinator.errors.ingress import (
    ApiDeliveryWorkerRejectedError,
    ApiDeliveryWorkerServerError,
    ApiDeliveryWorkerUnreachableError,
)
from ai.backend.common.api_handlers import BaseRequestModel
from ai.backend.common.dto.appproxy.v2.ingress.request import (
    IngressRemoveRequest,
    IngressUpsertRequest,
)
from ai.backend.common.dto.appproxy.v2.ingress.types import Ingress, IngressKey

_TOKEN_HEADER = "X-BackendAI-Token"


class ApiDeliveryWorkerClientPool:
    """Holds one ApiDeliveryWorkerClient per api-delivery worker address."""

    _secrets: SecretConfig
    _clients: dict[str, ApiDeliveryWorkerClient]

    def __init__(self, secrets: SecretConfig) -> None:
        self._secrets = secrets
        self._clients = {}

    def load_client(self, addr: str) -> ApiDeliveryWorkerClient:
        client = self._clients.get(addr)
        if client is None:
            session = aiohttp.ClientSession(
                base_url=f"http://{addr}",
                timeout=aiohttp.ClientTimeout(total=30.0, connect=10.0),
            )
            client = ApiDeliveryWorkerClient(session, addr, self._secrets)
            self._clients[addr] = client
        return client

    async def close(self) -> None:
        for client in self._clients.values():
            await client.close()
        self._clients.clear()


class ApiDeliveryWorkerClient:
    """Sends ingress pushes to the API port of one api-delivery worker node."""

    _session: aiohttp.ClientSession
    _addr: str
    _secrets: SecretConfig

    def __init__(self, session: aiohttp.ClientSession, addr: str, secrets: SecretConfig) -> None:
        self._session = session
        self._addr = addr
        self._secrets = secrets

    async def close(self) -> None:
        await self._session.close()

    async def upsert(self, ingresses: Sequence[Ingress]) -> None:
        await self._post("/v2/ingress/upsert", IngressUpsertRequest(ingresses=list(ingresses)))

    async def remove(self, keys: Sequence[IngressKey]) -> None:
        await self._post("/v2/ingress/remove", IngressRemoveRequest(keys=list(keys)))

    async def _post(self, path: str, request: BaseRequestModel) -> None:
        try:
            async with self._session.post(
                path,
                json=request.model_dump(mode="json"),
                headers={_TOKEN_HEADER: self._secrets.api_secret},
            ) as resp:
                body = await resp.read()
                extra_msg = f"worker {self._addr} answered {resp.status}"
                extra_data = {
                    "worker_addr": self._addr,
                    "status": resp.status,
                    "body": body.decode(errors="replace"),
                }
                match resp.status // 100:
                    case 4:
                        raise ApiDeliveryWorkerRejectedError(
                            extra_msg=extra_msg, extra_data=extra_data
                        )
                    case 5:
                        raise ApiDeliveryWorkerServerError(
                            extra_msg=extra_msg, extra_data=extra_data
                        )
        except aiohttp.ClientError as e:
            raise ApiDeliveryWorkerUnreachableError(
                extra_msg=f"worker {self._addr} is unreachable",
                extra_data={"worker_addr": self._addr},
            ) from e
