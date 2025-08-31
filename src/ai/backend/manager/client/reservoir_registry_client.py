from collections.abc import Mapping
from datetime import datetime
from typing import Any

import aiohttp
import yarl
from dateutil.tz import tzutc

from ai.backend.common.auth.utils import generate_signature
from ai.backend.manager.data.reservoir.types import ReservoirRegistryData

_HASH_TYPE = "sha256"


class ReservoirRegistryClient:
    """
    Client used to connect from one manager to another.
    Used when connecting to a remote reservoir service.
    """

    _registry_data: ReservoirRegistryData

    def __init__(self, registry_data: ReservoirRegistryData):
        self._registry_data = registry_data

    def _build_header(self, method: str, rel_url: str) -> Mapping[str, str]:
        date = datetime.now(tzutc())
        hdrs, _ = generate_signature(
            method=method,
            version=self._registry_data.api_version,
            endpoint=yarl.URL(self._registry_data.endpoint),
            date=date,
            rel_url=rel_url,
            content_type="application/json",
            access_key=self._registry_data.access_key,
            secret_key=self._registry_data.secret_key,
            hash_type=_HASH_TYPE,
        )

        return {
            "User-Agent": "Backend.AI Manager facing manager client",
            "Content-Type": "application/json",
            "X-BackendAI-Version": self._registry_data.api_version,
            "Date": date.isoformat(),
            **hdrs,
        }

    async def request(self, method: str, rel_url: str, **kwargs) -> Any:
        header = self._build_header(method=method, rel_url=rel_url)
        url = yarl.URL(self._registry_data.endpoint) / rel_url.lstrip("/")
        async with aiohttp.ClientSession() as session:
            async with session.request(method, str(url), headers=header, **kwargs) as response:
                response.raise_for_status()
                return await response.json()
