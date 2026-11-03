from dataclasses import dataclass
from typing import override

import aiohttp
from yarl import URL

from ai.backend.common.dto.appproxy.v2.ingress.types import Ingress

from .base import BaseBackend, BaseBackendArgs


@dataclass
class BackendConfig:
    hostname: str
    port: int
    domain: str | None = None


@dataclass(frozen=True)
class H2BackendArgs(BaseBackendArgs):
    api_endpoint: URL


class H2Backend(BaseBackend):
    _api_endpoint: URL

    def __init__(self, args: H2BackendArgs) -> None:
        super().__init__(args)
        self._api_endpoint = args.api_endpoint

    @override
    async def update_ingress(self, ingress: Ingress) -> None:
        await super().update_ingress(ingress)
        await self.update_config([
            BackendConfig(target.host, target.port)
            for target_group in ingress.backend.target_groups
            for target in target_group.targets
        ])

    async def update_config(self, backends: list[BackendConfig]) -> None:
        new_config = "\n".join([
            f"backend={b.hostname},{b.port};{b.domain or ''};proto=h2" for b in backends
        ])
        async with aiohttp.ClientSession(base_url=self._api_endpoint) as sess:
            async with sess.post("/api/v1beta1/backendconfig", data=new_config) as resp:
                resp.raise_for_status()
