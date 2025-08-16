from dataclasses import dataclass

import aiohttp
from yarl import URL

from .base import BaseBackend


@dataclass
class BackendConfig:
    hostname: str
    port: int
    domain: str | None = None


class H2Backend(BaseBackend):
    api_endpoint: URL

    def __init__(self, api_endpoint: URL, *args, **kwargs) -> None:
        super().__init__(*args, **kwargs)
        self.api_endpoint = api_endpoint

    async def update_config(self, backends: list[BackendConfig]) -> None:
        new_config = "\n".join([
            f"backend={b.hostname},{b.port};{b.domain or ''};proto=h2" for b in backends
        ])
        async with aiohttp.ClientSession(base_url=self.api_endpoint) as sess:
            async with sess.post("/api/v1beta1/backendconfig", data=new_config) as resp:
                resp.raise_for_status()
