import logging
from typing import AsyncIterator

import aiohttp
import yarl

from ai.backend.common.docker import get_docker_connector
from ai.backend.common.logging import BraceStyleAdapter

from .base import BaseContainerRegistry

log = BraceStyleAdapter(logging.getLogger(__spec__.name))  # type: ignore[name-defined]


class LocalRegistry(BaseContainerRegistry):
    async def prepare_client_session(self) -> AsyncIterator[tuple[yarl.URL, aiohttp.ClientSession]]:
        url, connector = get_docker_connector()
        async with aiohttp.ClientSession(connector=connector) as sess:
            yield url, sess

    async def fetch_repositories(
        self,
        sess: aiohttp.ClientSession,
    ) -> AsyncIterator[str]:
        async with sess.get(self.registry_url / "images/json") as response:
            items = await response.json()
            for item in items:
                labels = item["Labels"]
                if item["RepoTags"][0] == "<none>:<none>":
                    # cache images
                    continue
                if not labels:
                    continue
                if "ai.backend.kernelspec" in labels:
                    repo = item["RepoTags"][0]
                    yield repo
