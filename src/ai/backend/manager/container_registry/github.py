import logging
from typing import AsyncIterator, override

import aiohttp

from ai.backend.logging import BraceStyleAdapter
from ai.backend.manager.exceptions import ContainerRegistryProjectEmpty

from .base import (
    BaseContainerRegistry,
)

log = BraceStyleAdapter(logging.getLogger(__spec__.name))  # type: ignore[name-defined]


class GitHubRegistry(BaseContainerRegistry):
    @override
    async def fetch_repositories(self, sess: aiohttp.ClientSession) -> AsyncIterator[str]:
        if not self.registry_info.project:
            raise ContainerRegistryProjectEmpty(self.registry_info.type, self.registry_info.project)

        project = self.registry_info.project
        access_token = self.registry_info.password
        entity_type = self.registry_info.extra.get("entity_type", None)

        if entity_type is None:
            raise RuntimeError("Entity type is not provided for GitHub registry!")

        base_url = f"https://api.github.com/{entity_type}/{project}/packages"

        headers = {
            "Authorization": f"Bearer {access_token}",
            "Accept": "application/vnd.github.v3+json",
        }
        page = 1

        while True:
            async with sess.get(
                base_url,
                headers=headers,
                params={"package_type": "container", "per_page": 30, "page": page},
            ) as response:
                if response.status == 200:
                    data = await response.json()
                    for repo in data:
                        yield f"{project}/{repo['name']}"
                    if "next" in response.links:
                        page += 1
                    else:
                        break
                else:
                    raise RuntimeError(
                        f"Failed to fetch repositories! {response.status} error occured."
                    )
