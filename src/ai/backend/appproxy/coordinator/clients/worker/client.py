from __future__ import annotations

from collections.abc import Sequence
from typing import override

import aiohttp
from aiohttp import hdrs

from ai.backend.appproxy.common.config import HostPortPair, SecretConfig
from ai.backend.appproxy.coordinator.clients.worker.base import AbstractWorkerClient
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


class AppProxyWorkerClient(AbstractWorkerClient):
    """Sends ingress pushes to the API port of one worker node."""

    _session: aiohttp.ClientSession
    _addr: HostPortPair
    _secrets: SecretConfig

    def __init__(
        self, session: aiohttp.ClientSession, addr: HostPortPair, secrets: SecretConfig
    ) -> None:
        self._session = session
        self._addr = addr
        self._secrets = secrets

    @override
    async def upsert(self, ingresses: Sequence[Ingress]) -> None:
        await self._post_ingress_request(
            "/v2/ingress/upsert", IngressUpsertRequest(ingresses=list(ingresses))
        )

    @override
    async def remove(self, keys: Sequence[IngressKey]) -> None:
        await self._post_ingress_request(
            "/v2/ingress/remove", IngressRemoveRequest(keys=list(keys))
        )

    async def _post_ingress_request(self, path: str, request: BaseRequestModel) -> None:
        try:
            async with self._session.post(
                path,
                json=request.model_dump(mode="json"),
                headers={
                    hdrs.ACCEPT: "application/json",
                    _TOKEN_HEADER: self._secrets.api_secret,
                },
            ) as resp:
                body = await resp.read()
                extra_msg = f"worker {self._addr} answered {resp.status}"
                extra_data = {
                    "worker_addr": str(self._addr),
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
        except (aiohttp.ClientError, TimeoutError) as e:
            raise ApiDeliveryWorkerUnreachableError(
                extra_msg=f"worker {self._addr} is unreachable",
                extra_data={"worker_addr": str(self._addr)},
            ) from e
