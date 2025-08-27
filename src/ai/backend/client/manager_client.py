from collections.abc import Mapping
from datetime import datetime

import aiohttp
import yarl
from dateutil.tz import tzutc

from ai.backend.client.auth import generate_signature
from ai.backend.manager.data.reservoir.types import ReservoirRegistryData

HASH_TYPE = "sha256"


class ManagerFacingClient:
    """
    TODO: Write this.
    """

    _registry_data: ReservoirRegistryData

    def __init__(self, registry_data: ReservoirRegistryData):
        self._registry_data = registry_data

    def _build_header(self, method: str, rel_url: str) -> Mapping[str, str]:
        hdrs, _ = generate_signature(
            method=method,
            version=self._registry_data.api_version,
            endpoint=yarl.URL(self._registry_data.endpoint),
            date=datetime.now(tzutc()),
            rel_url=rel_url,
            content_type="application/json",
            access_key=self._registry_data.access_key,
            secret_key=self._registry_data.secret_key,
            hash_type=HASH_TYPE,
        )
        return hdrs

    async def request(self, method: str, rel_url: str) -> aiohttp.ClientResponse:
        header = self._build_header(method=method, rel_url=rel_url)
        url = yarl.URL(self._registry_data.endpoint) / rel_url

        async with aiohttp.ClientSession() as session:
            async with session.request(
                method,
                str(url),
                headers=header,
            ) as response:
                response.raise_for_status()
                return response
